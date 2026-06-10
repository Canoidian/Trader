# Project Plan

1. Analyze and write `PROJECT.md` at root. Include details on the architecture (Python based), project modules: `api`, `backtest`, `analysis`.
2. Determine API needs: Kraken python SDK or raw requests. For backtesting, mock data or fetch small historical data chunk.
3. Spawn an E2E testing orchestrator to write tests for Backtesting criteria (10 trades + fees + PnL) and Research criteria (3 coins ranked locally).
4. Spawn sub-orchestrators for:
   - Module 1: Kraken API integration & Backtest script.
   - Module 2: Self-Learning Analysis Script (technical indicators: RSI, MACD, etc. to rank coins).
5. Aggregate results and report completion.
