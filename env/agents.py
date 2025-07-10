import random
import numpy as np
from collections import deque
from env.trader_base import TraderBase

class NoisyTrader(TraderBase):
    def __init__(self, name, min_qty=1, max_qty=10, price_noise_std=0.01, bias_p=0.5):
        super().__init__(name)
        self.min_qty = min_qty # min quantity to buy
        self.max_qty = max_qty # max quantity to buy
        self.price_noise_std = price_noise_std # standard deviation used in determing random buy/sell price
        self.next = random.randint(100, 250) # how long to wait until next action
        self.bias_p = bias_p # upwards bias


    def step(self, lob, t):
        """
        One "action" for the trader
        Buy/sells a random amount of shares at a random price
        """
        if t < self.next:
            return

        side = 'buy' if random.random() < self.bias_p else 'sell'
        _, _, mid = lob.best_bid_ask()
        ref_price = mid if mid is not None else 100

        order_price = round(ref_price + random.gauss(0, self.price_noise_std), 2)

        rand = random.random()
        if rand < 0.075:
            qty = random.randint(self.min_qty * 10, self.max_qty * 2)
        elif rand < 0.25:
            qty = random.randint(self.min_qty, self.max_qty // 2)   
        else:
            qty = random.randint(self.min_qty, self.max_qty)

        if side == 'sell' and self.inventory == 0:
            self.next = t + random.randint(50, 200)
            return
        elif side == 'sell' and self.inventory < qty:
            qty = self.inventory
        elif side == 'buy' and self.inventory == self.max_inv:
            self.next = t + random.randint(50, 200)
            return
        elif side == 'buy' and self.inventory + qty > self.max_inv:
            qty = self.max_inv-self.inventory
        
        if rand < 0.25:
            lob.process_market_order(side, qty, owner=self)
        else:
            lob.add_limit_order(side, order_price, qty, owner=self)

        self.next = t + random.randint(100, 250)



class InformedTrader(TraderBase):
    def __init__(self, name, threshold=0, min_qty=1, max_qty=10):
        super().__init__(name)
        self.threshold = threshold # signal threshold
        self.min_qty = min_qty # mininum quantity traded
        self.max_qty = max_qty # maxmimum quantity traded
        self.midprice_history = deque(maxlen=100) # midprice history
        self.next = random.randint(50, 150) # time until next action


    def step(self, lob, t):
        """
        One "action" for trader
        Buys/sells shares using simple momentum strategy
        """
        _, _, mid = lob.best_bid_ask()
        if mid is None:
            return
        
        self.midprice_history.append(mid)

        if t < self.next or len(self.midprice_history) < 2:
            return
        
        delta = self.midprice_history[-1] - self.midprice_history[0]

        if delta > self.threshold:
            qty = random.randint(self.min_qty, self.max_qty)
            if self.inventory - qty >= -self.max_inv:
                lob.process_market_order('sell', qty, owner=self)

        if delta < -self.threshold:
            qty = random.randint(self.min_qty, self.max_qty)
            if self.inventory + qty <= self.max_inv:
                lob.process_market_order('buy', qty, owner=self)

        self.next = t + random.randint(50, 150)



class HeuristicMarketMaker(TraderBase):
    def __init__(self, name, spread=0.015, quote_freq=30):
        super().__init__(name)
        self.spread = spread # half spread
        self.order_size = self.mm_max_inv // 10 # fixed size per side
        self.quote_freq = quote_freq # frequency of quote refresh
        self.next = 0 # time of next quote refresh
        self.active_orders = set() # track order ids to cancel later

    def cancel_old_orders(self, lob):
        """
        Cancel all old active orders
        """
        for oid in list(self.active_orders):
            if oid in lob.order_map:
                del lob.order_map[oid]
        self.active_orders.clear()


    def step(self, lob, t):
        """
        One "action" for trader
        Submits buy/sells in order of the input spread
        """
        if t < self.next:
            return
        
        _, _, mid = lob.best_bid_ask()
        if mid is None:
            return
        
        self.cancel_old_orders(lob)

        skew = 2 * (self.inventory / self.mm_max_inv) * self.spread
        bid_price = round(mid - self.spread - skew, 2)
        ask_price = round(mid + self.spread - skew, 2)

        if self.inventory < self.mm_max_inv - self.order_size:
            bid_id = lob.add_limit_order('buy', bid_price, self.order_size, owner=self)
            self.active_orders.add(bid_id)
        
        if self.inventory > -self.mm_max_inv + self.order_size:
            ask_id = lob.add_limit_order('sell', ask_price, self.order_size, owner=self)
            self.active_orders.add(ask_id)

        self.next = t + self.quote_freq
    