import os
import math
import json
from typing import List, Dict, Any
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import SearchRequest, CalibrateRequest, SimulateRequest
from bloomberg import search_instruments, get_history_or_demo
from utils import (
    annualize_returns,
    compute_corr,
    simulate_portfolio_paths,
    summary_stats,
)

APP_TITLE = "Dockerized Portfolio Monte Carlo Simulator"

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ['*'] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search")
def api_search(req: SearchRequest):
    try:
        results = search_instruments(req.query, req.yellowKey, demo=DEMO_MODE)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.post("/api/calibrate")
def api_calibrate(req: CalibrateRequest):
    if not req.tickers:
        raise HTTPException(status_code=400, detail="tickers cannot be empty")

    try:
        df = get_history_or_demo(
            tickers=req.tickers,
            start=req.start,
            end=req.end,
            periodicity=req.periodicity,
            adjust_splits=req.adjustSplits,
            adjust_dividends=req.adjustDividends,
            use_total_return=req.useTotalReturnField,
            demo=DEMO_MODE,
        )
        # df columns -> MultiIndex: level0 ticker, data is PX_LAST or TR index
        # Align, forward-fill weekdays, drop rows with any NaN
        df = df.asfreq("B").ffill().dropna(how="any")

        # Compute daily log returns
        logret = np.log(df / df.shift(1)).dropna()

        mu, vol = annualize_returns(logret)
        corr = compute_corr(logret)

        params_per_ticker = {}
        last_prices = df.iloc[-1]
        for t in req.tickers:
            params_per_ticker[t] = {
                "S0": float(last_prices[t]),
                "mu": float(mu[t]),
                "vol": float(vol[t]),
            }

        return {
            "tickers": req.tickers,
            "paramsPerTicker": params_per_ticker,
            "corr": corr.tolist(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {e}")


@app.post("/api/simulate")
def api_simulate(req: SimulateRequest):
    try:
        if not req.positions:
            raise HTTPException(status_code=400, detail="positions cannot be empty")

        tickers = [p.ticker for p in req.positions]
        qty = np.array([p.qty for p in req.positions], dtype=float)

        # Calibration dict
        cal = req.calibration
        params = cal.get("paramsPerTicker", {})
        corr = np.array(cal.get("corr"), dtype=float)

        try:
            S0  = np.array([params[t]["S0"]  for t in tickers], dtype=float)
            mu  = np.array([params[t]["mu"]  for t in tickers], dtype=float)
            vol = np.array([params[t]["vol"] for t in tickers], dtype=float)
        except KeyError as ke:
            raise HTTPException(status_code=400, detail=f"Missing calibration for ticker: {ke}")

        N = len(tickers)
        if corr.shape != (N, N):
            raise HTTPException(
                status_code=400,
                detail=(f"Correlation matrix shape {corr.shape} does not match number of assets {N}. "
                        f"Did you pass nSims×nSims instead of assets×assets, or skip calibration?")
            )

        drift = np.zeros_like(mu) if req.driftMode == "flat" else mu

        paths_sample, pnl, pv0 = simulate_portfolio_paths(
            S0=S0,
            qty=qty,
            mu=drift,
            vol=vol,
            corr=corr,
            days=int(req.days),
            n_sims=int(req.nSims),
            use_student_t=req.useStudentT,
            dof=int(req.dof) if req.dof else 6,
            sample_paths_max=500,
        )

        summ = summary_stats(pnl)
        out = {
            "pv0": float(pv0),
            "pnl": pnl.tolist(),
            "pathsSample": [p.tolist() for p in paths_sample],
            "summary": {k: float(v) for k, v in summ.items()},
        }
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")


@app.get("/")
def root():
    return {"ok": True, "app": APP_TITLE, "demo": DEMO_MODE}