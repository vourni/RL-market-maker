import heapq
import uuid
from datetime import datetime as dt
from collections import defaultdict

class Order:
    def __init__(self, side, price, quantity, timestamp):
        self.id = uuid.uuid4()
        self.side = side #buy/sell
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp


class LOBSimulator:
    def __init__(self):
        self.bid_book = [] # max heap
        self.ask_book = [] # min heap
        self.order_map = {} # order_id -> Order
        self.trades = [] # list of all trades (price, quantity)


    def check_order_book(self, order):
        side = order.side

        if side == 'buy':
            book = self.ask_book
            best_price, _, order_id = heapq.heappop(book)
            best_order = self.order_map[order_id]

            if best_price <= order.price:
                trade_qty = min(order.quantity, best_order.quantity)
                order.quantity -= trade_qty
                best_order.quantity -= trade_qty

                self.trades.append((abs(best_price), trade_qty, order.timestamp))

                if best_order.quantity > 0:
                    heapq.heappush(book, (best_price, order_id))
                else:
                    del self.order_map[order_id]
            
            else:
                heapq.heappush(book, (best_price, order_id))

        else:
            book = self.bid_book
            best_price, _, order_id = heapq.heappop(book)
            best_order = self.order_map[order_id]

            if abs(best_price) >= order.price:
                trade_qty = min(order.quantity, best_order.quantity)
                order.quantity -= trade_qty
                best_order.quantity -= trade_qty

                self.trades.append((abs(best_price), trade_qty, order.timestamp))

                if best_order.quantity > 0:
                    heapq.heappush(book, (best_price, order_id))
                else:
                    del self.order_map[order_id]
            
            else:
                heapq.heappush(book, (best_price, order_id))


    def add_limit_order(self, side, price, quantity):
        timestamp = dt.now().timestamp()
        order = Order(side, price, quantity, timestamp)

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
    

    def best_bid_ask(self):
        best_bid = -self.bid_book[0][0] if self.bid_book else None
        best_ask = self.ask_book[0][0] if self.ask_book else None
        return best_bid, best_ask
    

if __name__ == '__main__':
    lob = LOBSimulator()

    lob.add_limit_order('buy', 100, 5)
    print(lob.best_bid_ask())
    lob.add_limit_order('buy', 100, 5)
    print(lob.best_bid_ask())
    lob.add_limit_order('sell', 100, 10)

    print(lob.best_bid_ask())
    print(lob.trades)
