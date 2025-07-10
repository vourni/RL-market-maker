import heapq
import uuid
import random
from datetime import datetime as dt
from collections import deque

class Order:
    def __init__(self, side, price, quantity, timestamp, owner=None):
        self.id = uuid.uuid4()
        self.side = side #buy/sell
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.owner = owner


class LOBSimulator:
    def __init__(self):
        self.bid_book = [] # max heap
        self.ask_book = [] # min heap
        self.order_map = {} # order_id -> Order
        self.trades = [] # list of all trades (price, quantity, timestamp)
        self.last_trade_price = None # tracks trade price


    def check_order_book(self, order):
        """
        Checks order book for mathcing orders to a submitted limit order
        Works in order of best price and then earliest timestamp
        """
        side = order.side
        book = self.ask_book if side == 'buy' else self.bid_book

        while order.quantity > 0 and book:
            best_price, best_order_timestamp, best_order_id = heapq.heappop(book)

            if best_order_id not in self.order_map:
                continue

            best_order = self.order_map[best_order_id]

            if (side == 'buy' and best_price <= order.price) or (side == 'sell' and -best_price >= order.price):
                trade_qty = min(order.quantity, best_order.quantity)
                order.quantity -= trade_qty
                best_order.quantity -= trade_qty

                self.last_trade_price = abs(best_price)
                self.trades.append((abs(best_price), trade_qty, order.timestamp))

                if order.owner:
                    order.owner.log_trade(order.side, self.last_trade_price, trade_qty)
                if best_order.owner:
                    best_order.owner.log_trade(best_order.side, self.last_trade_price, trade_qty)

                if best_order.quantity > 0:
                    heapq.heappush(book, (best_price, best_order_timestamp, best_order_id))
                else:
                    del self.order_map[best_order_id]
            
            else:
                heapq.heappush(book, (best_price, best_order_timestamp, best_order_id))
                break
            

    def add_limit_order(self, side, price, quantity, owner=None):
        """
        Adds a limit order to book
        Calls check order book to check if any trades match
        """
        timestamp = dt.now().timestamp()
        order = Order(side, price, quantity, timestamp, owner=owner)

        try:
            self.check_order_book(order)
        except:
            print('No orders in opposite side of order book')

        if side == 'buy' and order.quantity > 0:
            heapq.heappush(self.bid_book, (-price, timestamp, order.id)) # highest price = priority
        elif side == 'sell' and order.quantity > 0:
            heapq.heappush(self.ask_book, (price, timestamp, order.id)) # lowest price = priority
    
        self.order_map[order.id] = order

        return order.id
    

    def process_market_order(self, side, quantity, owner=None):
        """
        Processes a market order at best offer(s)
        """
        book = self.ask_book if side == 'buy' else self.bid_book

        while quantity > 0 and book:
            best_price, best_timestamp, order_id = heapq.heappop(book)

            if order_id not in self.order_map:
                continue

            order = self.order_map[order_id]
            trade_qty = min(order.quantity, quantity)
            quantity -= trade_qty
            order.quantity -= trade_qty

            self.last_trade_price = abs(best_price)
            self.trades.append((order.price, trade_qty, dt.now().timestamp()))

            if owner:
                owner.log_trade(side, self.last_trade_price, trade_qty)
            if order.owner:
                order.owner.log_trade(order.side, self.last_trade_price, trade_qty)

            if order.quantity > 0:
                heapq.heappush(book, (best_price, best_timestamp, order_id))
            else:
                del self.order_map[order_id]


    def cancel_random_order(self):
        """
        Deletes a random order from the book
        """
        if not self.order_map:
            return None
        
        order_id = random.choice(list(self.order_map.keys()))
        del self.order_map[order_id]
        return order_id
    

    def clean_order_books(self):
        self.bid_book = [
            (price, ts, oid)
            for (price, ts, oid) in self.bid_book
            if oid in self.order_map
        ]
        heapq.heapify(self.bid_book)

        self.ask_book = [
            (price, ts, oid)
            for (price, ts, oid) in self.ask_book
            if oid in self.order_map
        ]
        heapq.heapify(self.ask_book)
    

    def best_bid_ask(self):
        """
        Returns best bid and ask
        """
        best_bid = -self.bid_book[0][0] if self.bid_book else None
        best_ask = self.ask_book[0][0] if self.ask_book else None
        mid = (best_ask + best_bid)/2 if best_ask is not None and best_bid is not None else best_bid if best_bid is not None else best_ask if best_ask is not None else None
        return best_bid, best_ask, mid
