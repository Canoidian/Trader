import subprocess
import os
import sys

SCRIPT_BACKTEST = "scripts/run_backtest.py"
SCRIPT_ANALYSIS = "scripts/run_analysis.py"

# ==========================================
# Tier 1: Category-Partition
# Feature 1 (run_backtest.py)
# ==========================================

def test_f1_t1_profitable_run(profitable_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(profitable_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"
    assert "PnL" in result.stdout

def test_f1_t1_unprofitable_run(unprofitable_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(unprofitable_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"
    assert "PnL" in result.stdout

def test_f1_t1_zero_trades(zero_variance_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(zero_variance_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"
    assert "Fees = 0" in result.stdout or "0 trades" in result.stdout

def test_f1_t1_invalid_data(base_data_dir, run_script):
    # Corrupt one of the data files
    bad_file = base_data_dir / "BTC_historical.csv"
    with open(bad_file, 'w') as f:
        f.write("invalid data\ncorrupt\n")
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(base_data_dir))
    assert result.returncode != 0, "Expected failure on invalid data, but succeeded."

def test_f1_t1_single_direction_trades(single_direction_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(single_direction_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

# ==========================================
# Feature 2 (run_analysis.py)
# ==========================================

def test_f2_t1_basic_evaluation(three_coins_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"
    assert "ranked" in result.stdout.lower()

def test_f2_t1_extended_evaluation(five_coins_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(five_coins_dir), "--coins", "BTC,ETH,SOL,ADA,DOGE")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f2_t1_identical_data(identical_data_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(identical_data_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f2_t1_missing_coin_data(three_coins_dir, run_script):
    # Delete ETH data to trigger missing data scenario
    os.remove(three_coins_dir / "ETH_historical.csv")
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode != 0, "Expected failure on missing coin data."

def test_f2_t1_unsupported_ticker(three_coins_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "INVALIDCOIN")
    assert result.returncode != 0, "Expected failure on unsupported ticker."

# ==========================================
# Tier 2: Boundary Value Analysis
# Feature 1 (run_backtest.py)
# ==========================================

def test_f1_t2_exactly_10_trades(exact_10_trades_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(exact_10_trades_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f1_t2_zero_capital(base_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(base_data_dir), "--capital", "0")
    assert result.returncode != 0, "Expected failure with zero capital."

def test_f1_t2_fee_exceeds_profit(high_fees_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(high_fees_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f1_t2_high_frequency_volume(hft_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(hft_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f1_t2_micro_trades(micro_trades_data_dir, run_script):
    result = run_script(SCRIPT_BACKTEST, "--data-dir", str(micro_trades_data_dir))
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

# ==========================================
# Feature 2 (run_analysis.py)
# ==========================================

def test_f2_t2_exactly_3_coins(three_coins_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f2_t2_insufficient_coins(two_coins_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(two_coins_dir), "--coins", "BTC,ETH")
    assert result.returncode != 0, "Expected failure with insufficient coins."

def test_f2_t2_memory_limit_large_data(large_data_dir, run_script):
    # Pass 512MB limit in env
    env = os.environ.copy()
    env["MEMORY_LIMIT_MB"] = "512"
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(large_data_dir), "--coins", "BTC,ETH,SOL", env=env)
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f2_t2_minimal_data(minimal_data_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(minimal_data_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

def test_f2_t2_zero_variance_data(zero_variance_data_dir, run_script):
    result = run_script(SCRIPT_ANALYSIS, "--data-dir", str(zero_variance_data_dir), "--coins", "BTC,ETH,SOL")
    assert result.returncode == 0, f"Expected success but got error: {result.stderr}"

# ==========================================
# Tier 3: Pairwise Interactions
# ==========================================

def extract_coins_from_output(stdout, coins):
    found_coins = []
    # We look for words that might be tickers in the stdout
    for line in stdout.split('\n'):
        for word in line.replace(',', ' ').split():
            clean_word = word.strip('.:;')
            if clean_word in coins and clean_word not in found_coins:
                found_coins.append(clean_word)
    return found_coins

def test_f1f2_t3_feed_top_rank(three_coins_dir, run_script):
    coins = ["BTC", "ETH", "SOL"]
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", ",".join(coins))
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, coins)
    assert len(ranked_coins) > 0, "Could not parse top coin from analysis stdout"
    top_coin = ranked_coins[0]
    
    backtest_res = run_script(SCRIPT_BACKTEST, "--data-dir", str(three_coins_dir), "--coin", top_coin)
    assert backtest_res.returncode == 0, f"Backtest failed: {backtest_res.stderr}"

def test_f1f2_t3_feed_bottom_rank(three_coins_dir, run_script):
    coins = ["BTC", "ETH", "SOL"]
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", ",".join(coins))
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, coins)
    assert len(ranked_coins) > 0, "Could not parse bottom coin from analysis stdout"
    bottom_coin = ranked_coins[-1]
    
    backtest_res = run_script(SCRIPT_BACKTEST, "--data-dir", str(three_coins_dir), "--coin", bottom_coin)
    assert backtest_res.returncode == 0, f"Backtest failed: {backtest_res.stderr}"

def test_f1f2_t3_concurrent_execution(three_coins_dir):
    p1 = subprocess.Popen([sys.executable, SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen([sys.executable, SCRIPT_BACKTEST, "--data-dir", str(three_coins_dir), "--coin", "BTC"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    p1.wait()
    p2.wait()
    assert p1.returncode == 0, "Parallel analysis script failed"
    assert p2.returncode == 0, "Parallel backtest script failed"

def test_f1f2_t3_shared_data_dir(three_coins_dir, run_script):
    res1 = run_script(SCRIPT_ANALYSIS, "--data-dir", str(three_coins_dir), "--coins", "BTC,ETH,SOL")
    res2 = run_script(SCRIPT_BACKTEST, "--data-dir", str(three_coins_dir), "--coin", "BTC")
    assert res1.returncode == 0, f"Analysis script failed on shared directory: {res1.stderr}"
    assert res2.returncode == 0, f"Backtest script failed on shared directory: {res2.stderr}"

# ==========================================
# Tier 4: Workload / Scenarios
# ==========================================

def test_t4_bull_market_scenario(bull_market_data_dir, run_script):
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(bull_market_data_dir), "--coins", "BTC,ETH,SOL")
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, ["BTC", "ETH", "SOL"])
    assert len(ranked_coins) > 0, "Could not extract ranked coins"
    top_coin = ranked_coins[0]
    
    res = run_script(SCRIPT_BACKTEST, "--data-dir", str(bull_market_data_dir), "--coin", top_coin)
    assert res.returncode == 0, f"Backtest failed: {res.stderr}"

def test_t4_bear_market_scenario(bear_market_data_dir, run_script):
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(bear_market_data_dir), "--coins", "BTC,ETH,SOL")
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, ["BTC", "ETH", "SOL"])
    assert len(ranked_coins) > 0, "Could not extract ranked coins"
    top_coin = ranked_coins[0]

    res = run_script(SCRIPT_BACKTEST, "--data-dir", str(bear_market_data_dir), "--coin", top_coin)
    assert res.returncode == 0, f"Backtest failed: {res.stderr}"

def test_t4_crab_market_volatility(crab_market_data_dir, run_script):
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(crab_market_data_dir), "--coins", "BTC,ETH,SOL")
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, ["BTC", "ETH", "SOL"])
    assert len(ranked_coins) > 0, "Could not extract ranked coins"
    top_coin = ranked_coins[0]

    res = run_script(SCRIPT_BACKTEST, "--data-dir", str(crab_market_data_dir), "--coin", top_coin)
    assert res.returncode == 0, f"Backtest failed: {res.stderr}"

def test_t4_weekly_rebalance_loop(base_data_dir, run_script):
    for week in range(2):
        a_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(base_data_dir), "--coins", "BTC,ETH,SOL")
        assert a_res.returncode == 0, f"Analysis failed in loop: {a_res.stderr}"
        
        ranked_coins = extract_coins_from_output(a_res.stdout, ["BTC", "ETH", "SOL"])
        assert len(ranked_coins) > 0, "Could not extract ranked coins"
        top_coin = ranked_coins[0]
        
        b_res = run_script(SCRIPT_BACKTEST, "--data-dir", str(base_data_dir), "--coin", top_coin)
        assert b_res.returncode == 0, f"Backtest failed in loop: {b_res.stderr}"

def test_t4_analysis_fallback(zero_variance_data_dir, run_script):
    analysis_res = run_script(SCRIPT_ANALYSIS, "--data-dir", str(zero_variance_data_dir), "--coins", "BTC,ETH,SOL")
    assert analysis_res.returncode == 0, f"Analysis failed: {analysis_res.stderr}"
    
    ranked_coins = extract_coins_from_output(analysis_res.stdout, ["BTC", "ETH", "SOL"])
    
    if not ranked_coins:
        # Fallback to no coin, or maybe just a default backtest behavior where no coin is required
        backtest_res = run_script(SCRIPT_BACKTEST, "--data-dir", str(zero_variance_data_dir), "--coin", "")
        assert backtest_res.returncode == 0, f"Backtest failed: {backtest_res.stderr}"
    else:
        # If it returns coins anyway, run backtest on the top ranked
        backtest_res = run_script(SCRIPT_BACKTEST, "--data-dir", str(zero_variance_data_dir), "--coin", ranked_coins[0])
        assert backtest_res.returncode == 0, f"Backtest failed: {backtest_res.stderr}"
