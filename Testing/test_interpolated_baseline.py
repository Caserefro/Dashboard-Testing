"""
Empirical Baseline & Interpolation - Test Script
=================================================
Demonstrates how averaging historical sprints (N=10 points) removes noise,
allowing clean function approximation (PCHIP / Monotonic Spline Interpolation)
to create an "Expected Master Baseline".

Then demonstrates comparing an active "Live Sprint" against this baseline
and using Mirrored Inv-Sqrt regression to forecast the live sprint's finish!

Usage:
    python test_interpolated_baseline.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator, CubicSpline
from scipy.optimize import curve_fit

# -------------------------------------------------------------------------
# 1. SIMULATE HISTORICAL SPRINTS (12 Sprints, N=10 checkpoints each)
# -------------------------------------------------------------------------
np.random.seed(101)

N = 10
x_data = np.linspace(0, 100, N)
x_max = x_data.max()

# Underlying organization rhythm: Mirrored burndown (starts slow, fast finish)
true_a, true_c, true_d = 115.0, 3.0, 105.0
y_base = true_d - true_a / np.sqrt((x_max - x_data) + true_c)

num_sprints = 12
historical_sprints = []

for i in range(num_sprints):
    # Each sprint has random daily reporting noise and slight variance
    noise = np.random.normal(0, 4.5, size=N)
    # Ensure start is around 100 and end is around 0
    sprint_y = np.clip(y_base + noise, 0, 110)
    sprint_y[0] = np.random.normal(100, 2.0)
    sprint_y[-1] = np.maximum(0, np.random.normal(2.0, 3.0))
    historical_sprints.append(sprint_y)

historical_sprints = np.array(historical_sprints)

# -------------------------------------------------------------------------
# 2. THE MASTER PROFILE: Averaging per checkpoint across sprints
# -------------------------------------------------------------------------
y_avg = np.mean(historical_sprints, axis=0)

# Apply Interpolation to the averaged points!
# PCHIP guarantees monotonicity (strictly decreasing, no artificial ripples)
pchip_interp = PchipInterpolator(x_data, y_avg)

# Standard Cubic Spline for comparison (can sometimes ripple/wobble)
cubic_interp = CubicSpline(x_data, y_avg)


# -------------------------------------------------------------------------
# 3. SIMULATE A LIVE ACTIVE SPRINT (Currently at Checkpoint 6 of 10)
# -------------------------------------------------------------------------
live_checkpoints = 6
x_live = x_data[:live_checkpoints]

# Let's say this team is running slightly behind (higher remaining work)
live_noise = np.random.normal(0, 2.5, size=live_checkpoints)
y_live = (y_base[:live_checkpoints] * 1.08) + live_noise
y_live[0] = 100.0

# Fit Mirrored Inv-Sqrt Regression ONLY to the 6 live points to forecast end!
def mirrored_model(x, a, c, d):
    safe_denom = np.maximum(0.01, (x_max - x) + c)
    return d - a / np.sqrt(safe_denom)

try:
    popt, _ = curve_fit(mirrored_model, x_live, y_live, p0=[100, 2, 100], maxfev=10000)
    live_forecast_success = True
except Exception:
    live_forecast_success = False


# -------------------------------------------------------------------------
# 4. CONSOLE REPORT & VELOCITY DELTA
# -------------------------------------------------------------------------
print("=" * 68)
print(f"{'Checkpoint':<12} {'Hist. Average':<16} {'Live Sprint':<16} {'Status / Delta':<18}")
print("-" * 68)

for idx in range(N):
    x_val = x_data[idx]
    hist_val = y_avg[idx]
    
    if idx < live_checkpoints:
        live_val = y_live[idx]
        delta = live_val - hist_val
        status = f"BEHIND by {delta:+.1f}" if delta > 0 else f"AHEAD by {abs(delta):.1f}"
        print(f"Day {x_val:>5.1f}    {hist_val:>10.1f} pts   {live_val:>10.1f} pts   [{status}]")
    else:
        if live_forecast_success:
            pred_val = mirrored_model(x_val, *popt)
            print(f"Day {x_val:>5.1f}    {hist_val:>10.1f} pts   {pred_val:>10.1f} pts   [-- FORECAST --]")
        else:
            print(f"Day {x_val:>5.1f}    {hist_val:>10.1f} pts        N/A         [-- FORECAST --]")

print("=" * 68)
print("\n* Notice how averaging removed individual sprint noise!")
print("* PCHIP Interpolation creates a seamless, monotonic expected baseline.\n")


# -------------------------------------------------------------------------
# 5. PLOT RESULTS (2 Panels)
# -------------------------------------------------------------------------
x_smooth = np.linspace(0, x_max, 300)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# -- Left Panel: Historical Sprints -> Averaged Master Profile --
ax1 = axes[0]
for i, sprint in enumerate(historical_sprints):
    label = "Historical Sprints" if i == 0 else None
    ax1.plot(x_data, sprint, color="#b0b8c0", alpha=0.35, linewidth=1, label=label)

ax1.scatter(x_data, y_avg, color="black", s=40, zorder=5, label="Averaged Points (N=10)")
ax1.plot(x_smooth, pchip_interp(x_smooth), color="#1d3557", linewidth=2.5, 
         label="PCHIP Interpolation (Master Baseline)")
ax1.plot(x_smooth, cubic_interp(x_smooth), "--", color="#e63946", linewidth=1.2, alpha=0.7,
         label="Standard Spline (Notice slight ripples)")

ax1.set_xlabel("Sprint Progress (%)")
ax1.set_ylabel("Remaining Work (Points)")
ax1.set_title("1. Building the Master Baseline via Averaging & Interpolation")
ax1.legend(loc="lower left", fontsize=9)
ax1.grid(True, alpha=0.3)

# -- Right Panel: Live Sprint vs Master Baseline & Forecast --
ax2 = axes[1]
ax2.plot(x_smooth, pchip_interp(x_smooth), color="#1d3557", linewidth=2, linestyle="--",
         alpha=0.6, label="Master Baseline (Expected)")

# Plot Live Sprint Checkpoints
ax2.plot(x_live, y_live, "o-", color="#e63946", linewidth=2.5, markersize=7,
         label="Live Sprint (Actuals Day 0-50)")

# Plot Regression Forecast for remaining days
if live_forecast_success:
    x_future = np.linspace(x_live[-1], x_max, 100)
    ax2.plot(x_future, mirrored_model(x_future, *popt), ":", color="#e63946", linewidth=2.5,
             label="Mirrored Regression Forecast")
    
    # Highlight completion gap
    final_pred = mirrored_model(x_max, *popt)
    ax2.annotate(f"Projected Finish:\n{final_pred:.1f} pts remaining", 
                 xy=(x_max, final_pred), xytext=(x_max - 35, final_pred + 20),
                 arrowprops=dict(facecolor='#e63946', shrink=0.05, width=1, headwidth=6),
                 fontsize=9, fontweight="bold", color="#e63946")

ax2.set_xlabel("Sprint Progress (%)")
ax2.set_ylabel("Remaining Work (Points)")
ax2.set_title("2. Live Sprint Monitoring & Regression Forecasting")
ax2.legend(loc="lower left", fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("interpolated_baseline_test.png", dpi=150)
plt.show()

print("Plot saved to interpolated_baseline_test.png")
