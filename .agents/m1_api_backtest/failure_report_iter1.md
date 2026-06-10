# Iteration 1 Failure Report

The Forensic Auditor reported a CLEAN verdict.
Reviewers 1 and 2 APPROVED the code.

However, the Challengers found the following bugs:
1. **ZeroDivisionError**: If `open_price` is 0, the math `crypto_amount = (trade_size_fiat - buy_fee) / open_price` in `backtest.py` crashes.
2. **Negative Fees/Prices**: `calculate_fee` allows negative trade sizes, producing negative fees. Negative prices are not handled and produce negative fiat and crypto.
3. **Missing Balance Check**: The backtest simulates trades without checking if the user has enough initial balance, allowing final balances to silently go negative.
4. **Rate limits**: `api.py` raises exceptions on 429 without exponential backoff or retry logic.
5. **Fee Subtraction Flaw**: Math error on the buy side. The fee is calculated on the gross amount but then subtracted from it to get the executed volume. Kraken calculates fees on the *executed volume*. So it slightly over-charges.

Please investigate the codebase to fix these bugs.
