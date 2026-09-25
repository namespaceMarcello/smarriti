import numpy as np
import pytest


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="also run the slow statistical tests (~20 s each)")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: needs many particles to reach 4 SE; runs only with --runslow")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="slow: run with --runslow"))


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
