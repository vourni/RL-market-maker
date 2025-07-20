import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import random
import numpy as np
from env.lob_simulator import LOBSimulator
from env.agents import NoisyTrader, InformedTrader, HeuristicMarketMaker
from env.rl_agents import RLMarketMaker
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker

if __name__ == '__main__':
    RL_wins = 0
    for j in range(1,101):
        lob = LOBSimulator()
        agents = {
            **{f"NoisyTrader{i}" : NoisyTrader(f"NoisyTrader{i}", bias_p=random.uniform(0.48, 0.53)) for i in range(1, 21)},
            **{f"InformedTrader{i}" : InformedTrader(f"InformedTrader{i}") for i in range(1,4)},
            "MarketMaker1" : HeuristicMarketMaker("MarketMaker1"),
            "RLMarketMaker1" : RLMarketMaker("RLMarketMaker1")
        }

        for i in range(10):
            lob.add_limit_order('buy', 100 - i * 0.01, 10)
            lob.add_limit_order('sell', 100 + i * 0.01, 10)

        n = 100000 # steps
        for t in range(n):
            for agent in agents.values():
                agent.step(lob, t)
            if i % 100 == 0:
                lob.clean_order_books()

        if agents['RLMarketMaker1'].pnl > agents['MarketMaker1'].pnl:
            RL_wins += 1
        
        print('RL Win Percent: ', RL_wins/j)
