import sys
sys.path.insert(0, '/Users/williamisaak/Projects/KrakenTraderV2')
from krakentrader.api import calculate_fee

print("Testing actual calculate_fee")
# Test 1
tf = 100.0
est_rate = calculate_fee(tf) / tf
est_vol = tf / (1 + est_rate)
exact_rate = calculate_fee(est_vol) / est_vol
ev = tf / (1 + exact_rate)
bf = calculate_fee(ev)
print(f"tf={tf}, ev={ev}, bf={bf}, total={ev+bf}")

# Simulated tiered fee
def tiered_fee(vol):
    if vol >= 50: return vol * 0.0020
    if vol >= 49.9: return vol * 0.0040
    return vol * 0.0060

tf = 50.0
est_rate = tiered_fee(tf) / tf
est_vol = tf / (1 + est_rate)
exact_rate = tiered_fee(est_vol) / est_vol
ev = tf / (1 + exact_rate)
bf = tiered_fee(ev)
print(f"Tiered: tf={tf}, ev={ev}, bf={bf}, total={ev+bf}")
