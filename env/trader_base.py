class TraderBase:
    def __init__(self, name, max_inventory=50):
        self.name = name # trader name
        self.inventory = 20 # inventory 
        self.pnl = 0.0 # profit/loss
        self.max_inv = max_inventory # maximum shares allowed for each trader at once
        self.mm_max_inv = max_inventory * 4 # maximum shares allowed for each market maker at once


    def log_trade(self, side, price, qty):
        """
        Logs trade into inventory and pnl
        """
        if side == 'buy':
            self.pnl -= price * qty
            self.inventory += qty
        elif side == 'sell':
            self.pnl += price * qty
            self.inventory -= qty


    def mark_to_market(self, mid_price):
        """
        Used to check total earnings including inventory
        """
        if mid_price is None:
            return self.pnl
        return self.pnl + self.inventory * mid_price
    