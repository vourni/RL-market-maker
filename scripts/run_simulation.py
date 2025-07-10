import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import random
import numpy as np
from env.lob_simulator import LOBSimulator
from env.agents import NoisyTrader, InformedTrader, HeuristicMarketMaker
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker

if __name__ == '__main__':
    lob = LOBSimulator()
    agents = {
        **{f"NoisyTrader{i}" : NoisyTrader(f"NoisyTrader{i}", bias_p=random.uniform(0.48, 0.53)) for i in range(1, 21)},
        **{f"InformedTrader{i}" : InformedTrader(f"InformedTrader{i}") for i in range(1,4)},
        "MarketMaker1": HeuristicMarketMaker("MarketMaker1")
    }

    price_vector = []
    spreads = []

    for i in range(10):
        lob.add_limit_order('buy', 100 - i * 0.01, 10)
        lob.add_limit_order('sell', 100 + i * 0.01, 10)




    n = 1000000 # milliseconds

    last_mid = lob.best_bid_ask()[2]
    if last_mid is None:
        last_mid = 100

    for t in range(n): 
        for agent in agents.values():
            agent.step(lob, t)

        bid,ask,mid_price = lob.best_bid_ask()
        if mid_price is not None:
            last_mid = mid_price
        price_vector.append(last_mid)
        if bid is not None and ask is not None:
            spreads.append(ask-bid)

        if i % 100 == 0:
            lob.clean_order_books()
    



    fig, ax = plt.subplots()
    ax.plot(price_vector)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Mid Price')
    ax.set_title('Simulated Mid Price Over Time')
    plt.show()

    sum = 0
    for name, agent in agents.items():
        print(f"{name} inventory: {agent.inventory}")
        print(f"{name} pnl: {agent.pnl}")

    print(np.mean(spreads))