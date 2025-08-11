from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    yellowKey: str = Field(default="Equity")


class CalibrateRequest(BaseModel):
    tickers: List[str]
    start: str
    end: str
    periodicity: str = Field(default="DAILY")
    adjustSplits: bool = True
    adjustDividends: bool = True
    useTotalReturnField: bool = False


class Position(BaseModel):
    ticker: str
    qty: float


class SimulateRequest(BaseModel):
    positions: List[Position]
    days: int = 20
    nSims: int = 5000
    driftMode: str = Field(pattern=r"^(flat|useMu)$", default="flat")
    useStudentT: bool = True
    dof: Optional[int] = 6
    calibration: Dict