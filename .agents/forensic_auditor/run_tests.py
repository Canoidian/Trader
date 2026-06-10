import subprocess
import sys
res = subprocess.run([sys.executable, "-m", "pytest", "tests/e2e/test_e2e.py", "-v"], capture_output=True, text=True)
with open("pytest_output.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(res.stdout)
    f.write("\nSTDERR:\n")
    f.write(res.stderr)
