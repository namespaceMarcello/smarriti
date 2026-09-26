"""WGS84 <-> UTM (Krueger series, mm accuracy within a zone). pyproj is blocked by Smart App Control."""
import numpy as np

A, F = 6378137.0, 1 / 298.257223563
K0, E0 = 0.9996, 500000.0
N_ = F / (2 - F)
A_HAT = A / (1 + N_) * (1 + N_**2 / 4 + N_**4 / 64)
ALPHA = (N_ / 2 - 2 * N_**2 / 3 + 5 * N_**3 / 16, 13 * N_**2 / 48 - 3 * N_**3 / 5, 61 * N_**3 / 240)
BETA = (N_ / 2 - 2 * N_**2 / 3 + 37 * N_**3 / 96, N_**2 / 48 + N_**3 / 15, 17 * N_**3 / 480)
DELTA = (2 * N_ - 2 * N_**2 / 3 - 2 * N_**3, 7 * N_**2 / 3 - 8 * N_**3 / 5, 56 * N_**3 / 15)
E2 = 2 * np.sqrt(N_) / (1 + N_)  # first eccentricity


def to_utm(lat, lon, zone):
    lat, lon = np.radians(np.asarray(lat, float)), np.asarray(lon, float)
    lam = np.radians(lon - (zone * 6 - 183))
    t = np.sinh(np.arctanh(np.sin(lat)) - E2 * np.arctanh(E2 * np.sin(lat)))
    xi = np.arctan2(t, np.cos(lam))
    eta = np.arctanh(np.sin(lam) / np.sqrt(1 + t**2))
    x, y = eta.copy(), xi.copy()
    for j, a in enumerate(ALPHA, 1):
        x += a * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
        y += a * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
    return E0 + K0 * A_HAT * x, K0 * A_HAT * y


def from_utm(e, n, zone):
    xi = np.asarray(n, float) / (K0 * A_HAT)
    eta = (np.asarray(e, float) - E0) / (K0 * A_HAT)
    xp, ep = xi.copy(), eta.copy()
    for j, b in enumerate(BETA, 1):
        xp -= b * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
        ep -= b * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
    chi = np.arcsin(np.sin(xp) / np.cosh(ep))
    lat = chi.copy()
    for j, d in enumerate(DELTA, 1):
        lat += d * np.sin(2 * j * chi)
    lon = (zone * 6 - 183) + np.degrees(np.arctan2(np.sinh(ep), np.cos(xp)))
    return np.degrees(lat), lon
