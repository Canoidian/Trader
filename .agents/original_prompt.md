## 2026-06-08T12:43:54Z

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Get user approval → delegate to teamwork_preview

A live-trading crypto bot for Kraken that executes small, volatile trades with real but low capital, strictly factoring in trading fees. It features self-learning capabilities to research coins and adapt to the market.

Working directory: ~/teamwork_projects/kraken_bot
Integrity mode: development

## Requirements

### R1. Kraken Execution & Fee Awareness
The bot must connect to Kraken via API to execute trades. Its profitability logic must explicitly account for Kraken's fee structure to ensure it doesn't lose money on small, volatile trades.

### R2. Self-Learning & Lightweight Research
The bot must implement an analysis strategy to research coins and adapt to market conditions. The approach must be computationally efficient enough to run continuously on an older Mac Mini without excessive resource consumption.

## Acceptance Criteria

### Execution & Fee Verification
- [ ] The project includes a backtesting script that simulates at least 10 trades using historical Kraken data.
- [ ] The simulation explicitly subtracts Kraken trading fees for each simulated trade.
- [ ] The script outputs a final PnL (Profit and Loss) summary proving the fee calculation works.

### Research Verification
- [ ] The project includes an analysis script that evaluates at least 3 different coins and outputs a ranked recommendation.
- [ ] The analysis runs completely locally and executes successfully without high memory/GPU requirements.
