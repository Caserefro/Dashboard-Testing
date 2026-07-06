"""
Baseline-Anchored Forecasting - Test Script
============================================
Demonstrates why forecasting from early/mid-sprint data (N=6 points) fails
with unconstrained regression, and how "Shape-Locked Regression" and 
"Delta Decay Forecasting" solve it cleanly!

Usage:
    python test_anchored_forecasting.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.optimize import curve_fit

# -------------------------------------------------------------------------
# 1. GENERATE HISTORICAL MASTER BASELINE (from 12 sprints)
# -------------------------------------------------------------------------
np.random.seed(42)

N = 10
x_data = np.linspace(0, 100, N)
x_max = x_data.max()

# True organizational burndown rhythm (Mirrored / Deadline Rush)
true_a, true_c, true_d = 120.0, 3.0, 110.0
y_base = true_d - true_a / np.sqrt((x_max - x_data) + true_c)

# Simulate 12 historical sprints and take the mean
hist_sprints = [y_base + np.random.normal(0, 4.0, size=N) for _ in range(12)]
y_avg = np.mean(hist_sprints, axis=0)
y_avg[0] = 100.0  # Normalize start
y_avg[-1] = 0.0   # Normalize end

# Master Baseline Interpolator (PCHIP)
pchip_baseline = PchipInterpolator(x_data, y_avg)


# -------------------------------------------------------------------------
# 2. SIMULATE A LIVE ACTIVE SPRINT (At Checkpoint 6 of 10 -> Day 55.6)
# -------------------------------------------------------------------------
live_idx = 6
x_live = x_data[:live_idx]

# This sprint starts slower and is running ~10 points BEHIND schedule
y_live = y_avg[:live_idx] + np.array([0.0, 3.5, 6.2, 9.1, 11.4, 10.8])
current_delta = y_live[-1] - y_avg[live_idx - 1]  # Gap at Day 55.6 (~ +10.8 pts)


# -------------------------------------------------------------------------
# 3. IMPLEMENT THE 3 FORECASTING METHODS (For Days 66.7 to 100)
# -------------------------------------------------------------------------

def mirrored_model(x, a, c, d):
    safe_denom = np.maximum(0.01, (x_max - x) + c)
    return d - a / np.sqrt(safe_denom)

# -- METHOD 1: Unconstrained Regression (The Old Way) --
# Letting all 3 params float on just 6 flat points (ill-posed!)
try:
    popt_unconstrained, _ = curve_fit(mirrored_model, x_live, y_live, p0=[100, 2, 100], maxfev=15000)
    unconstrained_success = True
except Exception:
    unconstrained_success = False
    popt_unconstrained = [0, 1, 0]  # dummy values if failed

# -- METHOD 2: Shape-Locked Regression (Anchored to Master Baseline) --
# Step 1: Fit the FULL master baseline (all 10 points) to get the organization's true shape
popt_master, _ = curve_fit(mirrored_model, x_data, y_avg, p0=[100, 2, 100])
master_a, master_c, master_d = popt_master

# Step 2: Lock ALL 3 shape parameters. Fit ONLY a single vertical shift 's'
# on the live data. This preserves the exact historical curvature!
def shifted_master_model(x, s):
    """Master curve + vertical shift. Only 1 free parameter!"""
    return mirrored_model(x, master_a, master_c, master_d) + s

popt_shift, _ = curve_fit(shifted_master_model, x_live, y_live, p0=[5.0])
vertical_shift = popt_shift[0]

# For plotting: the shape-locked forecast is just the master curve shifted vertically
def shape_locked_forecast(x):
    return mirrored_model(x, master_a, master_c, master_d) + vertical_shift

# -- METHOD 3: Agile Delta Forecasting (Catch-Up Track vs Slip Track) --
x_future = x_data[live_idx-1:] # From Day 55.6 to 100

# 3A. Slip Track: Assume the +10.8 pt gap persists (parallel finish)
slip_forecast = pchip_baseline(x_future) + current_delta

# 3B. Catch-Up Track: Assume team accelerates to close the gap linearly by Day 100
decay_weights = (x_max - x_future) / (x_max - x_future[0])
catchup_forecast = pchip_baseline(x_future) + (current_delta * decay_weights)


# -------------------------------------------------------------------------
# 4. CONSOLE COMPARISON REPORT
# -------------------------------------------------------------------------
print("=" * 84)
print(f"{'Day':<6} {'Master Base':<13} {'Live Actual':<13} {'1. Unconstrained':<18} {'2. Shape-Locked':<16} {'3. Catch-Up':<13}")
print("-" * 84)

for i in range(N):
    x_val = x_data[i]
    base_val = y_avg[i]
    
    if i < live_idx:
        live_val = y_live[i]
        print(f"{x_val:>5.1f}  {base_val:>10.1f} pt  {live_val:>10.1f} pt       --                 --              --")
    else:
        m1_str = f"{mirrored_model(x_val, *popt_unconstrained):>10.1f} pt" if unconstrained_success else "    FAILED"
        m2_val = shape_locked_forecast(x_val)
        m3_val = catchup_forecast[i - (live_idx - 1)]
        print(f"{x_val:>5.1f}  {base_val:>10.1f} pt       --       {m1_str:<18} {m2_val:>10.1f} pt      {m3_val:>10.1f} pt")

print("=" * 84)
print(f"\n* Notice at Day 100:")
if unconstrained_success:
    print(f"  - Unconstrained (Old): {mirrored_model(100, *popt_unconstrained):.1f} pts (Can overshoot or dive erratically due to 6 flat points!)")
else:
    print(f"  - Unconstrained (Old): FAILED TO CONVERGE! (Exceeded 15,000 iterations! Ultimate proof of instability!)")
print(f"  - Shape-Locked (New):  {shape_locked_forecast(100):.1f} pts (Smooth, realistic - master curve shifted by {vertical_shift:+.1f} pts!)")
print(f"  - Catch-Up Track:      0.0 pts (Tapers the +10.8 pt gap exactly to zero by deadline)\n")


# -------------------------------------------------------------------------
# 5. PLOT RESULTS (2 Panels)
# -------------------------------------------------------------------------
x_smooth = np.linspace(0, x_max, 300)
x_smooth_future = np.linspace(x_live[-1], x_max, 150)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# -- Left Panel: Unconstrained vs Shape-Locked Regression --
ax1 = axes[0]
ax1.plot(x_smooth, pchip_baseline(x_smooth), "--", color="#8d99ae", linewidth=2, label="Master Baseline (PCHIP)")
ax1.plot(x_live, y_live, "o-", color="#d90429", linewidth=2.5, markersize=7, label="Live Sprint (Day 0-55)")

# Plot Unconstrained Forecast
if unconstrained_success:
    ax1.plot(x_smooth_future, mirrored_model(x_smooth_future, *popt_unconstrained), ":", 
             color="#ffb703", linewidth=2.5, label="1. Unconstrained Regression (Old Way)")

# Plot Shape-Locked Forecast (master curve + vertical shift)
ax1.plot(x_smooth_future, shape_locked_forecast(x_smooth_future), "-", 
         color="#2a9d8f", linewidth=3, label=f"2. Shape-Locked (shift={vertical_shift:+.1f})")

# Also show the full shape-locked curve from Day 0 for context
ax1.plot(x_smooth, shape_locked_forecast(x_smooth), "-", color="#2a9d8f", linewidth=1, alpha=0.3)

ax1.set_xlabel("Sprint Progress (%)")
ax1.set_ylabel("Remaining Work (Points)")
ax1.set_title("Method 1 vs Method 2: Why Shape-Locking Stabilizes Forecasts")
ax1.legend(loc="lower left", fontsize=9)
ax1.grid(True, alpha=0.3)

# -- Right Panel: Agile Delta Forecasting (Catch-Up vs Slip Track) --
ax2 = axes[1]
ax2.plot(x_smooth, pchip_baseline(x_smooth), "--", color="#8d99ae", linewidth=2, label="Master Baseline (PCHIP)")
ax2.plot(x_live, y_live, "o-", color="#d90429", linewidth=2.5, markersize=7, label="Live Sprint (Day 0-55)")

# Plot Slip Track
ax2.plot(x_future, slip_forecast, "--", color="#e76f51", linewidth=2.5, 
         label=f"3A. Slip Track (+{current_delta:.1f} pts behind at deadline)")

# Plot Catch-Up Track
ax2.plot(x_future, catchup_forecast, "-", color="#1d3557", linewidth=3, 
         label="3B. Catch-Up Track (Tapers delta to 0 by deadline)")

# Highlight finish gap
ax2.annotate(f"Slip Finish:\n{slip_forecast[-1]:.1f} pts left", xy=(100, slip_forecast[-1]), 
             xytext=(65, slip_forecast[-1] + 15),
             arrowprops=dict(facecolor='#e76f51', shrink=0.05, width=1, headwidth=5),
             fontsize=9, fontweight="bold", color="#e76f51")

ax2.set_xlabel("Sprint Progress (%)")
ax2.set_ylabel("Remaining Work (Points)")
ax2.set_title("Method 3: Agile Delta Forecasting (Catch-Up vs Slip Scenarios)")
ax2.legend(loc="lower left", fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("anchored_forecasting_test.png", dpi=150)
plt.show()

print("Plot saved to anchored_forecasting_test.png")
