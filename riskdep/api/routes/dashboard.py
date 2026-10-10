"""`GET /api/vault/{address}` and `GET /api/market/{id}` — a vault and a market, read live."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ... import dashboard as D
from ... import sources as S
from ..artifacts import fetch_lock
from ..schemas import Market, Vault

router = APIRouter(tags=["dashboard"])


def _read(fn, key: str) -> Any:
    with fetch_lock:
        try:
            return fn(S.Fetcher("direct"), key)
        except S.SourceError as e:
            raise HTTPException(status_code=502, detail=f"data source error: {e}") from e


@router.get("/api/vault/{address}", response_model=Vault)
def get_vault(address: str) -> Any:
    """A Vault V2: its Blue markets by allocation, and the liquidations of their borrowers."""
    return _read(D.vault, address)


@router.get("/api/market/{market_id}", response_model=Market)
def get_market(market_id: str) -> Any:
    """A Blue market: its state and the liquidating fall of every borrower."""
    return _read(D.market, market_id)
