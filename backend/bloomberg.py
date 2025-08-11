"""Bloomberg connectivity helpers with DEMO fallbacks.

This module keeps all blpapi-specific logic isolated. In DEMO mode, it returns
mocked data so the app can run without entitlements.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

import numpy as np
import pandas as pd

SESSION_MODE = os.getenv("SESSION_MODE", "SERVER").upper()
BBG_HOST = os.getenv("BBG_HOST", "localhost")
BBG_PORT = int(os.getenv("BBG_PORT", "8194"))

# Lazily import blpapi so the container can run in demo mode without it installed
try:
    import blpapi  # type: ignore
except Exception:  # pragma: no cover
    blpapi = None


# ---------------------- DEMO DATA ----------------------

def _demo_search(query: str, yellow_key: str) -> List[Dict[str, str]]:
    universe = [
        ("AAPL US Equity", "Apple Inc"),
        ("MSFT US Equity", "Microsoft Corp"),
        ("GOOGL US Equity", "Alphabet Inc Class A"),
        ("AMZN US Equity", "Amazon.com Inc"),
        ("TSLA US Equity", "Tesla Inc"),
        ("NVDA US Equity", "NVIDIA Corp"),
        ("SPY US Equity", "SPDR S&P 500 ETF Trust"),
        ("QQQ US Equity", "Invesco QQQ Trust"),
        ("META US Equity", "Meta Universe")
    ]
    q = query.lower()
    results = [
        {"security": s, "description": d}
        for s, d in universe
        if q in s.lower() or q in d.lower()
    ]
    return results[:20]


def _demo_history(tickers: List[str], start: str, end: str, use_total_return: bool) -> pd.DataFrame:
    rng = pd.date_range(start=start, end=end, freq="B")
    out = {}
    rs = np.random.RandomState(abs(hash("|".join(tickers))) % (2**32))
    for t in tickers:
        drift = rs.uniform(0.05, 0.12) / 252.0
        vol = rs.uniform(0.15, 0.35) / np.sqrt(252.0)
        shocks = rs.normal(0, 1, size=len(rng)) * vol + drift
        prices = 100 * np.exp(np.cumsum(shocks))
        out[t] = pd.Series(prices, index=rng)
    df = pd.DataFrame(out)
    return df


# ---------------------- LIVE SEARCH ----------------------

def _live_search(query: str, yellow_key: str) -> List[Dict[str, str]]:
    if blpapi is None:
        raise RuntimeError("blpapi not available in this environment")

    session = _open_session()
    try:
        service = session.openService("//blp/instruments")
        svc = session.getService("//blp/instruments")
        # InstrumentListRequest
        req = svc.createRequest("instrumentListRequest")
        req.set("query", query)
        # yellowKey: e.g., "Equity", "Corp", etc.
        if yellow_key:
            req.set("yellowKeyFilter", yellow_key)
        req.set("maxResults", 20)

        cid = session.sendRequest(req)
        results = []
        while True:
            ev = session.nextEvent(5000)
            for msg in ev:
                if msg.correlationIds()[0].value() != cid.value():
                    continue
                if msg.messageType() == blpapi.Name("InstrumentListResponse"):
                    for inst in msg.getElement("instrumentList").values():
                        sec = inst.getElementAsString("security")
                        desc = inst.getElementAsString("description")
                        results.append({"security": sec, "description": desc})
                    return results
                if ev.eventType() == blpapi.Event.RESPONSE:
                    return results
    finally:
        session.stop()


# ---------------------- LIVE HISTORY ----------------------

def _live_history(tickers: List[str], start: str, end: str, use_total_return: bool) -> pd.DataFrame:
    if blpapi is None:
        raise RuntimeError("blpapi not available in this environment")

    field = "TOT_RETURN_INDEX_GROSS_DVDS" if use_total_return else "PX_LAST"

    session = _open_session()
    try:
        session.openService("//blp/refdata")
        svc = session.getService("//blp/refdata")
        req = svc.createRequest("HistoricalDataRequest")
        for t in tickers:
            req.getElement("securities").appendValue(t)
        req.getElement("fields").appendValue(field)
        req.set("startDate", start.replace("-", ""))
        req.set("endDate", end.replace("-", ""))
        req.set("periodicitySelection", "DAILY")
        # Adjustment flags
        req.set("adjustmentSplit", True)
        req.set("adjustmentAbnormal", True)
        req.set("adjustmentNormal", True)
        req.set("adjustmentFollowDPDF", True)

        cid = session.sendRequest(req)
        data = {}
        while True:
            ev = session.nextEvent(5000)
            for msg in ev:
                if msg.correlationIds()[0].value() != cid.value():
                    continue
                if msg.messageType() == blpapi.Name("HistoricalDataResponse"):
                    sec_data_array = msg.getElement("securityData")
                    sec = sec_data_array.getElementAsString("security")
                    fdata = sec_data_array.getElement("fieldData")
                    dt_vals = []
                    px_vals = []
                    for row in fdata.values():
                        dt_vals.append(row.getElementAsDatetime("date").date())
                        px_vals.append(row.getElementAsFloat(field))
                    s = pd.Series(px_vals, index=pd.to_datetime(dt_vals))
                    data[sec] = s
                if ev.eventType() == blpapi.Event.RESPONSE:
                    df = pd.DataFrame(data).sort_index()
                    return df
    finally:
        session.stop()


# ---------------------- PUBLIC API ----------------------

def search_instruments(query: str, yellow_key: str, demo: bool = False) -> List[Dict[str, str]]:
    if demo:
        return _demo_search(query, yellow_key)
    return _live_search(query, yellow_key)


def get_history_or_demo(
    tickers: List[str],
    start: str,
    end: str,
    periodicity: str,
    adjust_splits: bool,
    adjust_dividends: bool,
    use_total_return: bool,
    demo: bool,
) -> pd.DataFrame:
    if demo:
        return _demo_history(tickers, start, end, use_total_return)
    return _live_history(tickers, start, end, use_total_return)


# ---------------------- SESSION ----------------------

def _open_session():
    if blpapi is None:
        raise RuntimeError("blpapi not available")

    if SESSION_MODE == "SERVER":
        sess_opts = blpapi.SessionOptions()
        sess_opts.setServerHost(BBG_HOST)
        sess_opts.setServerPort(BBG_PORT)
        session = blpapi.Session(sess_opts)
    elif SESSION_MODE == "DESKTOP":
        session = blpapi.Session()
    else:
        raise RuntimeError(f"Unknown SESSION_MODE={SESSION_MODE}")

    if not session.start():
        raise RuntimeError("Failed to start Bloomberg session")
    return session