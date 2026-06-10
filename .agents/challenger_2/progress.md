# Progress Report

- Investigated the current state of `krakentrader/api.py` and `krakentrader/backtest.py`.
- Analyzed the two-pass algorithm for calculating the fee and executed volume in `backtest.py`.
- Derived the exact mathematical formulas for flat and piecewise linear fee tiers.
- Confirmed that `executed_volume_fiat + buy_fee` equals exactly `trade_size_fiat` for the current flat fee, resulting in zero leakage and zero overcharging.
- Stress-tested the algorithm against theoretical tiered structures (as required by "applying Kraken fee tier structures explicitly") and proved that it correctly resolves boundary crossovers without overcharging, unless tier thresholds are pathologically close (separated by less than the fee itself, which is not true for Kraken).
- Verified `balance` tracking and PnL calculation logic. It correctly subtracts exactly `trade_size_fiat` and adds `net_return`. `balance` bounds are safe.
- Ready to report findings.

Last visited: 2026-06-08T16:35:00Z
