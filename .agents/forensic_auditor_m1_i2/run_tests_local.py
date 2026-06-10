import pytest
import sys

if __name__ == "__main__":
    exit_code = pytest.main(["tests/e2e/test_e2e.py", "-v"])
    with open("test_results.log", "w") as f:
        f.write(f"Exit code: {exit_code}\n")
