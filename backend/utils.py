from __future__ import annotations
import numpy as np
import pandas as pd


def annualize_returns(logret: pd.DataFrame):
    mean_daily = logret.mean()
    std_daily = logret.std(ddof=1)
    mu = mean_daily * 252.0
    vol = std_daily * np.sqrt(252.0)
    return mu, vol


def compute_corr(logret: pd.DataFrame) -> np.ndarray:
    return np.asarray(logret.corr())


def _stable_cholesky(corr: np.ndarray) -> np.ndarray:
    # Add tiny jitter if needed to ensure positive definiteness
    eps = 1e-10
    try:
        return np.linalg.cholesky(corr)
    except np.linalg.LinAlgError:
        d = np.diag(np.diag(corr))
        for k in range(10):
            try:
                L = np.linalg.cholesky(corr + eps * (k + 1) * d)
                return L
            except np.linalg.LinAlgError:
                continue
        raise


def simulate_portfolio_paths(
    S0: np.ndarray,
    qty: np.ndarray,
    mu: np.ndarray,
    vol: np.ndarray,
    corr: np.ndarray,
    days: int,
    n_sims: int,
    use_student_t: bool,
    dof: int,
    sample_paths_max: int = 500,
):
    """
    Returns:
      paths_sample: (min(n_sims, sample_paths_max), days) PV series per sample path
      pnl: (n_sims,) final PnL
      pv0: scalar current PV
    """
    assert S0.ndim == qty.ndim == mu.ndim == vol.ndim == 1
    n_assets = S0.shape[0]

    if corr.shape != (n_assets, n_assets):
        raise ValueError(f"corr must be {n_assets}x{n_assets}, got {corr.shape}")

    dt = 1.0 / 252.0
    vol_dt = vol * np.sqrt(dt)              # (N,)
    drift_dt = (mu - 0.5 * vol * vol) * dt  # (N,)

    L = _stable_cholesky(corr)              # (N,N)

    # Initialize log-prices
    logS0 = np.log(S0)                       # (N,)
    logS = np.empty((n_sims, days + 1, n_assets), dtype=float)
    logS[:, 0, :] = logS0                    # broadcast to (n_sims, N)

    rng = np.random.default_rng()

    # Student-t scaling per simulation (elliptical heavy tails)
    if use_student_t:
        g = rng.chisquare(dof, size=(n_sims,)) / dof   # (n_sims,)
        scale = 1.0 / np.sqrt(g)                       # (n_sims,)
    else:
        scale = np.ones(n_sims, dtype=float)

    for t in range(1, days + 1):
        z = rng.normal(0.0, 1.0, size=(n_sims, n_assets))   # (S,N)
        z_corr = z @ L.T                                    # (S,N)
        z_corr *= scale[:, None]                            # (S,N)
        incr = drift_dt[None, :] + vol_dt[None, :] * z_corr # (S,N)
        logS[:, t, :] = logS[:, t - 1, :] + incr            # (S,N)

    S = np.exp(logS)  # (S, T+1, N)

    # Portfolio PV per path/day
    pv = (S * qty.reshape(1, 1, -1)).sum(axis=2)  # (S, T+1)
    pv0 = pv[:, 0].mean()  # same across sims, but average to be robust

    pnl = pv[:, -1] - pv[:, 0]

    # pathsSample: up to sample_paths_max sims, exclude day0 for plotting clarity
    k = min(n_sims, sample_paths_max)
    idx = np.linspace(0, n_sims - 1, k, dtype=int)
    paths_sample = pv[idx, 1:]

    return paths_sample, pnl, float(pv0)


def summary_stats(pnl: np.ndarray):
    mean = pnl.mean()
    stdev = pnl.std(ddof=1)
    var95 = np.percentile(pnl, 5)
    es95 = pnl[pnl <= var95].mean() if (pnl <= var95).any() else var95
    prob_loss = float((pnl < 0).mean())
    return {
        "mean": mean,
        "stdev": stdev,
        "VaR95": var95,
        "ES95": es95,
        "probLoss": prob_loss,
    }