import sys
import traceback
from krakentrader.api import calculate_fee
from krakentrader.backtest import run_backtest

def run_tests():
    errors = []

    print("Test 1: calculate_fee with negative trade size")
    try:
        fee = calculate_fee(-100)
        print(f"  Fee for -100: {fee}")
        if fee < 0:
            print("  [FAIL] Fee is negative. Expected an absolute fee or exception.")
            errors.append("Negative fee allowed")
    except Exception as e:
        print(f"  [PASS] Exception raised: {e}")

    print("\nTest 2: run_backtest with zero open price")
    try:
        data_zero_open = [
            [1600000000, "0.0", "1.0", "0.0", "1.0", "0.5", "100", 10],
            [1600000000, "0.0", "1.0", "0.0", "1.0", "0.5", "100", 10]
        ]
        run_backtest(data_zero_open, num_trades=1)
        print("  [FAIL] Expected ZeroDivisionError but none occurred.")
        errors.append("ZeroDivisionError not handled")
    except ZeroDivisionError as e:
        print(f"  [PASS] Caught ZeroDivisionError: {e}")
    except Exception as e:
        print(f"  [FAIL] Caught unexpected exception: {e}")

    print("\nTest 3: run_backtest with negative price")
    try:
        data_negative_open = [
            [1600000000, "-10.0", "1.0", "10.0", "1.0", "0.5", "100", 10],
            [1600000000, "-10.0", "1.0", "10.0", "1.0", "0.5", "100", 10]
        ]
        res = run_backtest(data_negative_open, num_trades=1)
        print("  [FAIL] Negative price produced a trade result instead of handling the edge case.")
        errors.append("Negative price allowed")
    except Exception as e:
        print(f"  [PASS] Exception or handled result: {e}")

    print("\nTest 4: run_backtest with insufficient balance")
    try:
        data_normal = [
            [1600000000, "10.0", "10.0", "10.0", "10.0", "0.5", "100", 10],
            [1600000000, "10.0", "10.0", "10.0", "10.0", "0.5", "100", 10]
        ]
        res = run_backtest(data_normal, initial_balance=50.0, num_trades=1)
        if res['final_balance'] < 0:
            print(f"  [FAIL] Final balance went negative: {res['final_balance']}")
            errors.append("Negative balance allowed")
        else:
            print("  [PASS] Balance handled properly.")
    except Exception as e:
        print(f"  [FAIL] Unexpected exception: {e}")

    return len(errors)

if __name__ == "__main__":
    if run_tests() > 0:
        sys.exit(1)
    sys.exit(0)
