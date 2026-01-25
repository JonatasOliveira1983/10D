"""Utility functions for signal handling.
- `is_elite_signal(signal) -> bool`
- `compute_trade_qty(balance: float, price: float) -> float`
- `should_use_limit(signal) -> bool`
"""
from typing import Dict


def is_elite_signal(signal: Dict) -> bool:
    """Return True if the signal is marked as elite.
    Expected key: `is_elite` (bool). If missing, defaults to False.
    """
    return bool(signal.get("is_elite", False))


def compute_trade_qty(balance: float, price: float) -> float:
    """Calculate the quantity for a trade using 20 % of the unified balance.
    The quantity is `max_exposure / price`.
    """
    max_exposure = balance * 0.20
    if price == 0:
        return 0.0
    return max_exposure / price


def should_use_limit(signal: Dict) -> bool:
    """Decide whether to place a limit order.
    Simple heuristic: if `volatility` > 0.5 % (0.005) use limit, else market.
    """
    volatility = float(signal.get("volatility", 0))
    return volatility > 0.005
