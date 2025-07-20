from env.trader_base import TraderBase
import random
import numpy as np

class RLMarketMaker(TraderBase):
    def __init__(self, name, spread=0.015, quote_freq=30, learning_rate=0.2, discount=0.9, epsilon=0.1):
        super().__init__(name)
        self.spread = spread # min spread
        self.order_size = self.mm_max_inv // 20 # order_size
        self.quote_freq = quote_freq # frequency of quote refresh
        self.next = 0 # next quote refresh
        self.active_orders = set() # active orders
        self.q_table = {}  # state-action Q-values
        self.alpha = learning_rate # learning rate
        self.gamma = discount # discount for future rewards
        self.epsilon = epsilon # for prob
        self.actions = ['widen', 'narrow', 'shift_up', 'shift_down', 'do_nothing']
        self.prev_state = None # rpevious state
        self.prev_action = None # previous action
        self.prev_mid = None  # previous mid price

    def get_state(self, mid):
        """
        Condenses environment into a finite state space
        """
        inventory_bucket = int(self.inventory / 10) 
        price_bucket = int(mid * 10) 

        return (inventory_bucket, price_bucket)

    def choose_action(self, state):
        """
        Chooses next action randomly 10% of the time and the best action the rest
        """
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        return max(self.q_table[state], key=self.q_table[state].get)

    def update_q(self, reward, new_state):
        """
        Updates Q-table using the Bellman equation
        """
        if self.prev_state is None or self.prev_action is None:
            return
        
        if self.prev_state not in self.q_table:
            self.q_table[self.prev_state] = {a: 0.0 for a in self.actions}

        if new_state not in self.q_table:
            self.q_table[new_state] = {a: 0.0 for a in self.q_table[self.prev_state]}

        old_value = self.q_table[self.prev_state][self.prev_action]
        best_future = max(self.q_table[new_state].values())
        self.q_table[self.prev_state][self.prev_action] = (
            old_value + self.alpha * (reward + self.gamma * best_future - old_value)
        )

    def cancel_old_orders(self, lob):
        """
        Cancels old orders
        """
        for oid in list(self.active_orders):
            if oid in lob.order_map:
                del lob.order_map[oid]
        self.active_orders.clear()

    def step(self, lob, t):
        """
        Performs the same core market maker actions
        Uses the current state, a (price * 10, inventory(1-10)) tuple, to select the best or a random action
        Then updates the q table with the resulting reward of this state
        """
        if t < self.next:
            return

        _, _, mid = lob.best_bid_ask()
        if mid is None:
            return

        state = self.get_state(mid)
        action = self.choose_action(state)

        self.cancel_old_orders(lob)

        adjusted_spread = self.spread
        skew = 2 * (self.inventory / self.max_inv) * self.spread

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

        if self.inventory < self.mm_max_inv - self.order_size:
            bid_id = lob.add_limit_order('buy', bid_price, self.order_size, owner=self)
            self.active_orders.add(bid_id)
        if self.inventory > -self.mm_max_inv + self.order_size:
            ask_id = lob.add_limit_order('sell', ask_price, self.order_size, owner=self)
            self.active_orders.add(ask_id)

        reward = 0
        if self.prev_mid is not None:
            reward += (self.pnl - self.mark_to_market(self.prev_mid)) - 0.001 * abs(self.inventory)

        if self.prev_state is not None:
            self.update_q(reward, state)

        self.prev_state = state
        self.prev_action = action
        self.prev_mid = mid
        self.next = t + self.quote_freq
