# RL Market Maker Simulation

This project simulates a limit order book (LOB) market environment with multiple types of trading agents, including a reinforcement learning (RL) market maker. The framework allows testing and comparing the performance of RL-driven market-making strategies against heuristic or rule-based agents.

---

## 🚀 Features
- **LOB Simulator** (`lob_simulator.py`): Simulates a limit order book with order submissions, executions, and cancellations.
- **Trader Base** (`trader_base.py`): Abstract base class for all traders, ensuring consistent behavior.
- **Agents** (`agents.py`): Implements heuristic traders (e.g., momentum, mean reversion, random agents).
- **RL Agents** (`rl_agents.py`): Implements reinforcement learning-based market makers.
- **Run Simulation** (`run_simulation.py`): Main entry point to run experiments and compare strategies.

---

## 📊 Results
In experiments comparing the RL market maker to heuristic agents:
- **RL agent won 71% of the time** across repeated simulations.
- RL achieved higher average profitability and better adaptability to changing market conditions.

---