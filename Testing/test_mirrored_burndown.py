"""
Mirrored Burndown Curve Fitting - Test Script
==============================================
Tests curve fitting for burndown data that is "mirrored in both X and Y axes"
compared to a standard inverse square root.

A standard inverse-square-root burndown drops very fast at the beginning
and flattens out at the end (concave up).
When mirrored in BOTH X and Y axes (180-degree rotation / point reflection),
the curve starts high and flat (slow decrease) and drops VERY FAST at the end
(concave down).

Usage:
    python test_mirrored_burndown.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def r2_score(y_true, y_pred):
    """Calculate R-squared without sklearn."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot

# -------------------------------------------------------------------------
# 1. SYNTHETIC DATA: Mirrored in both X and Y axes
# -------------------------------------------------------------------------
np.random.seed(42)

N = 10
x_data = np.linspace(0, 100, N)
x_max = x_data.max()

# Ground Truth: Mirrored inverse square root
# y = d - a / sqrt((x_max - x) + c)
TRUE_A = 120.0
TRUE_C = 3.0
TRUE_D = 110.0

y_clean = TRUE_D - TRUE_A / np.sqrt((x_max - x_data) + TRUE_C)

# Add Gaussian noise (~4% of amplitude)
noise_std = 0.04 * (y_clean.max() - y_clean.min())
y_data = y_clean + np.random.normal(0, noise_std, size=N)


# -------------------------------------------------------------------------
# 2. CANDIDATE MODELS (Handling مختلف orientations)
# -------------------------------------------------------------------------

def mirrored_inv_sqrt(x, a, c, d):
    """Mirrored in X and Y: starts flat, drops fast at the end."""
    # max(0.01, ...) prevents division by zero or negative sqrt during fitting
    safe_denom = np.maximum(0.01, (x_max - x) + c)
    return d - a / np.sqrt(safe_denom)

def standard_inv_sqrt(x, a, c, d):
    """Standard inv-sqrt: drops fast at start, flattens at end."""
    safe_denom = np.maximum(0.01, x + c)
    return a / np.sqrt(safe_denom) + d

def quadratic_model(x, a, b, c):
    """Parabolic burndown (often fits slow-start / fast-end very well)."""
    return a * (x**2) + b * x + c

def mirrored_power_law(x, a, b, d):
    """General mirrored power law: d - a * (x_max - x)^b"""
    safe_base = np.maximum(0.01, (x_max - x))
    return d - a * np.power(safe_base, b)

def elliptical_burndown(x, a, d):
    """Quarter-ellipse: starts perfectly flat, drops vertically at x_max."""
    ratio = np.clip(x / x_max, -1.0, 1.0)
    return d + a * np.sqrt(1.0 - ratio**2)


MODELS = {
    "Mirrored Inv-Sqrt":  (mirrored_inv_sqrt,  [100, 2, 100]),
    # "Mirrored Power Law": (mirrored_power_law, [10, -0.5, 100]),
    # "Quadratic (x^2)":    (quadratic_model,    [-0.01, 0, 100]),
    # "Elliptical":         (elliptical_burndown,[80, 10]),
    # "Standard Inv-Sqrt":  (standard_inv_sqrt,  [80, 2, 10]),
}


# -------------------------------------------------------------------------
# 3. FIT & COMPARE
# -------------------------------------------------------------------------

results = {}

print("=" * 66)
print(f"{'Model':<20} {'R^2':>8}   Fitted parameters")
print("-" * 66)

for name, (func, p0) in MODELS.items():
    try:
        popt, pcov = curve_fit(func, x_data, y_data, p0=p0, maxfev=15000)
        y_pred = func(x_data, *popt)
        r2 = r2_score(y_data, y_pred)
        perr = np.sqrt(np.diag(pcov))
        results[name] = (func, popt, r2, perr)

        param_str = ", ".join(f"{v:+.3f}+/-{e:.3f}" for v, e in zip(popt, perr))
        print(f"{name:<20} {r2:>8.5f}   [{param_str}]")
    except Exception as e:
        print(f"{name:<20}  ** failed to converge **")

print("=" * 66)

best_name = max(results, key=lambda k: results[k][2])
print(f"\n* Best fit: {best_name}  (R^2 = {results[best_name][2]:.5f})\n")


# -------------------------------------------------------------------------
# 4. PLOT RESULTS
# -------------------------------------------------------------------------

x_smooth = np.linspace(0, x_max, 500)

fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [2, 1]})

# Left panel: Data vs Fitted Curves
ax = axes[0]
ax.scatter(x_data, y_data, s=25, color="#333333", alpha=0.7, label="Mirrored Data", zorder=5)
ax.plot(x_data, y_clean, "--", color="#999999", linewidth=1.5, label="Ground Truth", zorder=4)

colors = ["#e63946", "#2a9d8f", "#457b9d", "#f4a261", "#8d99ae"]
for (name, (func, popt, r2, _)), color in zip(results.items(), colors):
    ax.plot(x_smooth, func(x_smooth, *popt), linewidth=2, color=color,
            label=f"{name} (R^2={r2:.4f})")

ax.set_xlabel("x (Time / Iterations)")
ax.set_ylabel("y (Remaining Work)")
ax.set_title("Mirrored Burndown Curve - Model Comparison")
ax.legend(fontsize=9, loc="lower left")
ax.grid(True, alpha=0.3)

# Right panel: Residuals for Best Model
ax2 = axes[1]
best_func, best_popt, best_r2, _ = results[best_name]
residuals = y_data - best_func(x_data, *best_popt)
ax2.stem(x_data, residuals, linefmt="-", markerfmt="o", basefmt="k-")
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xlabel("x")
ax2.set_ylabel("Residual Error")
ax2.set_title(f"Residuals - {best_name}")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("mirrored_burndown_fit.png", dpi=150)
plt.show()

print("Plot saved to mirrored_burndown_fit.png")
