from trader_base import TraderBase
import random
import numpy as np

class RLMarketMaker(TraderBase):
    def __init__(self, name, spread=0.02, order_size=5, quote_freq=50, learning_rate=0.1, discount=0.95, epsilon=0.1):
        super().__init__(name)
        self.spread = spread
        self.order_size = order_size
        self.quote_freq = quote_freq
        self.next = random.randint(10, 50)
        self.active_orders = set()

        # RL-specific
        self.q_table = {}  # state-action Q-values
        self.alpha = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        self.prev_state = None
        self.prev_action = None
        self.prev_mid = None

    def get_state(self, mid):
        inventory_bucket = int(self.inventory / 10)  # discretize inventory
        price_bucket = int(mid * 10)  # bucket mid price
        return (inventory_bucket, price_bucket)

    def choose_action(self, state):
        actions = ['widen', 'narrow', 'shift_up', 'shift_down', 'do_nothing']
        if random.random() < self.epsilon:
            return random.choice(actions)
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in actions}
        return max(self.q_table[state], key=self.q_table[state].get)

    def update_q(self, reward, new_state):
        if self.prev_state is None or self.prev_action is None:
            return
        if new_state not in self.q_table:
            self.q_table[new_state] = {a: 0.0 for a in self.q_table[self.prev_state]}

        old_value = self.q_table[self.prev_state][self.prev_action]
        best_future = max(self.q_table[new_state].values())
        self.q_table[self.prev_state][self.prev_action] = (
            old_value + self.alpha * (reward + self.gamma * best_future - old_value)
        )

    def cancel_old_orders(self, lob):
        for oid in list(self.active_orders):
            if oid in lob.order_map:
                del lob.order_map[oid]
        self.active_orders.clear()

    def step(self, lob, t):
        if t < self.next:
            return

        _, _, mid = lob.best_bid_ask()
        if mid is None:
            return

        # RL: state, action
        state = self.get_state(mid)
        action = self.choose_action(state)

        # Cancel old quotes
        self.cancel_old_orders(lob)

        # Determine spread/action response
        adjusted_spread = self.spread
        skew = (self.inventory / self.max_inv) * self.spread

        if action == 'widen':
            adjusted_spread += 0.01
        elif action == 'narrow':
            adjusted_spread = max(0.005, self.spread - 0.01)
        elif action == 'shift_up':
            skew -= 0.01
        elif action == 'shift_down':
            skew += 0.01

        bid_price = round(mid - adjusted_spread - skew, 2)
        ask_price = round(mid + adjusted_spread - skew, 2)

        if self.inventory < self.max_inv:
            bid_id = lob.add_limit_order('buy', bid_price, self.order_size, owner=self)
            self.active_orders.add(bid_id)
        if self.inventory > -self.max_inv:
            ask_id = lob.add_limit_order('sell', ask_price, self.order_size, owner=self)
            self.active_orders.add(ask_id)

        # Reward based on profit delta and inventory penalty
        reward = 0
        if self.prev_mid is not None:
            reward += (self.pnl - self.mark_to_market(self.prev_mid))  # realized/unrealized PnL
            reward -= 0.001 * abs(self.inventory)  # penalize excess inventory

        if self.prev_state is not None:
            self.update_q(reward, state)

        self.prev_state = state
        self.prev_action = action
        self.prev_mid = mid
        self.next = t + self.quote_freq