# Original User Request

## Initial Request — 2026-06-08T08:44:59-04:00

You are the Project Orchestrator. 

Working directory: /Users/williamisaak/Projects/KrakenTraderV2

Your mission is to build a live-trading crypto bot for Kraken that executes small, volatile trades with real but low capital, strictly factoring in trading fees. It features self-learning capabilities to research coins and adapt to the market.

Requirements:
R1. Kraken Execution & Fee Awareness: Connect to Kraken via API to execute trades. Profitability logic must explicitly account for Kraken's fee structure to avoid losing money on small trades.
R2. Self-Learning & Lightweight Research: Implement an analysis strategy to research coins and adapt to market conditions. Must be computationally efficient enough to run continuously on an older Mac Mini.

Acceptance Criteria:
Execution & Fee Verification
- The project includes a backtesting script that simulates at least 10 trades using historical Kraken data.
- The simulation explicitly subtracts Kraken trading fees for each simulated trade.
- The script outputs a final PnL (Profit and Loss) summary proving the fee calculation works.

Research Verification
- The project includes an analysis script that evaluates at least 3 different coins and outputs a ranked recommendation.
- The analysis runs completely locally and executes successfully without high memory/GPU requirements.

Please set up your agent directory at /Users/williamisaak/Projects/KrakenTraderV2/.agents/orchestrator, maintain plan.md and progress.md, and delegate to specialized subagents to fulfill this request. Keep progress.md regularly updated so I can monitor your status. When you have met all acceptance criteria, claim victory and I will spawn the Victory Auditor.
