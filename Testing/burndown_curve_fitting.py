"""
Burndown Curve Fitting - Test Script
=====================================
Generates synthetic data that follows an inverse-square-root burndown shape,
adds realistic noise, then fits several candidate models and compares them.

Usage:
    python burndown_curve_fitting.py

Dependencies:
    pip install numpy scipy matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def r2_score(y_true, y_pred):
    """R-squared without sklearn."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot

# ──────────────────────────────────────────────
# 1.  SYNTHETIC DATA GENERATION
# ──────────────────────────────────────────────

np.random.seed(42)

N = 10                          # number of data points
x_data = np.linspace(1, 100, N) # avoid x=0 to keep 1/sqrt(x) finite

# Ground truth: a burndown that looks like  a/sqrt(x+c) + d
TRUE_A, TRUE_C, TRUE_D = 80.0, 2.0, 5.0
y_clean = TRUE_A / np.sqrt(x_data + TRUE_C) + TRUE_D

# Add Gaussian noise (~5% of signal amplitude)
noise_std = 0.05 * (y_clean.max() - y_clean.min())
y_data = y_clean + np.random.normal(0, noise_std, size=N)


# ──────────────────────────────────────────────
# 2.  CANDIDATE MODELS
# ──────────────────────────────────────────────

def inv_sqrt_model(x, a, c, d):
    """a / sqrt(x + c) + d"""
    return a / np.sqrt(x + c) + d

def power_law(x, a, b, d):
    """a * x^b + d   (b ~ -0.5 => inverse sqrt)"""
    return a * np.power(x, b) + d

def exp_decay(x, a, b, d):
    """a * e^(-bx) + d"""
    return a * np.exp(-b * x) + d

def reciprocal(x, a, c, d):
    """a / (x + c) + d   (steeper 1/x decay)"""
    return a / (x + c) + d

def log_decay(x, a, b, d):
    """a - b * ln(x + 1) + d"""
    return a - b * np.log(x + 1) + d


MODELS = {
    "Inv. sqrt(x)":  (inv_sqrt_model, [80, 2, 5]),
    "Power law":      (power_law,      [80, -0.5, 5]),
    "Exponential":    (exp_decay,      [50, 0.05, 5]),
    "Reciprocal 1/x": (reciprocal,    [200, 2, 5]),
    "Logarithmic":    (log_decay,      [50, 8, 5]),
}


# ──────────────────────────────────────────────
# 3.  FIT & COMPARE
# ──────────────────────────────────────────────

results = {}

print("=" * 62)
print(f"{'Model':<18} {'R^2':>8}   Fitted parameters")
print("-" * 62)

for name, (func, p0) in MODELS.items():
    try:
        popt, pcov = curve_fit(func, x_data, y_data, p0=p0, maxfev=10_000)
        y_pred = func(x_data, *popt)
        r2 = r2_score(y_data, y_pred)
        perr = np.sqrt(np.diag(pcov))  # 1-sigma parameter uncertainties
        results[name] = (func, popt, r2, perr)

        param_str = ", ".join(f"{v:+.4f}+/-{e:.4f}" for v, e in zip(popt, perr))
        print(f"{name:<18} {r2:>8.5f}   [{param_str}]")
    except RuntimeError:
        print(f"{name:<18}  ** failed to converge **")

print("=" * 62)

# Best model
best_name = max(results, key=lambda k: results[k][2])
print(f"\n*  Best fit: {best_name}  (R^2 = {results[best_name][2]:.5f})\n")


# ──────────────────────────────────────────────
# 4.  PLOT
# ──────────────────────────────────────────────

x_smooth = np.linspace(x_data.min(), x_data.max(), 500)

fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [2, 1]})

# -- Left panel: data + fitted curves --
ax = axes[0]
ax.scatter(x_data, y_data, s=20, color="#555", alpha=0.6, label="Noisy data", zorder=5)
ax.plot(x_data, y_clean, "--", color="#aaa", linewidth=1, label="Ground truth", zorder=4)

colors = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#f4a261"]
for (name, (func, popt, r2, _)), color in zip(results.items(), colors):
    ax.plot(x_smooth, func(x_smooth, *popt), linewidth=2, color=color,
            label=f"{name}  (R^2={r2:.4f})")

ax.set_xlabel("x  (e.g. time / iteration)")
ax.set_ylabel("y  (e.g. remaining work)")
ax.set_title("Burndown Curve - Model Comparison")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# -- Right panel: residuals for best model --
ax2 = axes[1]
best_func, best_popt, best_r2, _ = results[best_name]
residuals = y_data - best_func(x_data, *best_popt)
ax2.stem(x_data, residuals, linefmt="-", markerfmt="o", basefmt="k-")
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xlabel("x")
ax2.set_ylabel("Residual")
ax2.set_title(f"Residuals - {best_name}")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("burndown_fit_results.png", dpi=150)
plt.show()

print("Plot saved to burndown_fit_results.png")
