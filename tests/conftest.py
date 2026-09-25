import numpy as np


def quantile_ci(values, q, z=4.0):
    """Distribution-free interval for the q-quantile from order statistics (+-z binomial SE)."""
    v = np.sort(np.asarray(values)[~np.isnan(values)])
    n = len(v)
    half = z * np.sqrt(n * q * (1 - q))
    lo = v[max(0, int(np.floor(n * q - half)))]
    hi = v[min(n - 1, int(np.ceil(n * q + half)))]
    return float(lo), float(hi)


def within(ci, target, tol):
    return target * (1 - tol) <= ci[0] and ci[1] <= target * (1 + tol)
