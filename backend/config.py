"""
CryptoFastSignals - Configuration
"""

# =============================================================================
# INDICATOR SETTINGS
# =============================================================================

# EMA Settings (Updated from SMA)
EMA_FAST_PERIOD = 20
EMA_SLOW_PERIOD = 50

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands Settings
BB_PERIOD = 20
BB_STD_DEV = 2

# Pivot Point S. Trend Settings
PIVOT_PERIOD = 1
ATR_FACTOR = 2
ATR_PERIOD = 10

# Volume Settings
VOLUME_THRESHOLD = 1.2  # 1.2x average volume
VOLUME_LOOKBACK = 20    # Last 20 candles for average
VOLUME_CLIMAX_THRESHOLD = 3.0 # 3.0x average volume for exit

# RSI Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30       # Back to standard 30
RSI_OVERBOUGHT = 70     # Back to standard 70

# Pullback Settings
PULLBACK_THRESHOLD = 0.005  # 0.5% - price within this distance from EMA

# Institutional Settings (Judas Swing & Absorption)
JUDAS_ATR_MIN = 0.5
JUDAS_ATR_MAX = 1.5
JUDAS_RECLAIM_CANDLES = 3
JUDAS_WICK_PERCENT = 50
RS_LOOKBACK = 14
RS_MIN_THRESHOLD = 0.0  # Must be positive for LONG

# Absorption Logic
ABSORPTION_LOOKBACK = 3
ABSORPTION_CVD_RATIO = 0.2 # CVD Change / Candle Volume
SFP_WICK_PERCENT = 60

# Liquidity Hunt Settings
LSR_LONG_HEAVY = 1.5    # Above = too many longs, whales will hunt their stops
LSR_SHORT_HEAVY = 0.7   # Below = too many shorts, whales will hunt their stops
OI_HIGH_MULTIPLIER = 1.2  # OI 20% above average = high liquidation potential

# =============================================================================
# S/R SETTINGS
# =============================================================================

SR_PROXIMITY_THRESHOLD = 0.005  # 0.5% distance
SR_LOOKBACK_DAYS = 20           # 20 days for high/low

# =============================================================================
# TRADING SETTINGS
# =============================================================================
# Trading Settings
STOP_LOSS_PERCENT = 0.01   # 1%
TAKE_PROFIT_PERCENT = 0.02  # 2%
MIN_LEVERAGE = 50           # Minimum 50x leverage required
HISTORY_RETENTION_HOURS = 72 # 3 days

# Signal Freshness Settings
SIGNAL_TTL_MINUTES = 120     # 120 minutes for cleanup (2 hours)
ENTRY_ZONE_IDEAL = 0.002    # 0.2%
ENTRY_ZONE_LATE = 0.005     # 0.5%
ENTRY_MISSED_PERCENT = 0.01 # 1%

# Pair settings
PAIR_LIMIT = 100            # Monitor top 100 pairs by volume
EXCLUDED_PAIRS = [          # Pairs to exclude from monitoring
    "BTCUSDT",              # BTC leads the market, we follow it, not trade it
]

# =============================================================================
# SCORING SETTINGS
# =============================================================================

# Base scores for signal types
SCORE_EMA_CROSSOVER = 35        # EMA 20 crosses EMA 50 (Higher priority)
SCORE_TREND_PULLBACK = 25       # Pullback to EMA during trend
SCORE_RSI_BB_REVERSAL = 30      # RSI + BB Reversal
SCORE_INSTITUTIONAL_JUDAS = 45  # Stop Hunt + Reclaim (Institutional)

# Confirmation bonuses
SCORE_VOLUME_CONFIRMED = 15
SCORE_MACD_CONFIRMED = 20
SCORE_4H_TREND_ALIGNED = 30     # Critical filter
SCORE_PIVOT_CONFIRMED = 15
SCORE_SR_ALIGNED = 20
SCORE_SR_MISALIGNED = -20
SCORE_CVD_DIVERGENCE = 15
SCORE_OI_ACCUMULATION = 15
SCORE_LSR_CLEANUP = 10
SCORE_ABSORPTION_CONFIRMED = 20
SCORE_RSI_CROSSOVER_BTC = 25    # ALT RSI crosses above BTC RSI (decoupling)
SCORE_LIQUIDITY_ALIGNED = 30    # Signal aligns with predicted liquidity hunt direction

# =============================================================================
# API SETTINGS
# =============================================================================

BYBIT_BASE_URL = "https://api.bybit.com"
UPDATE_INTERVAL_SECONDS = 5  # Scan every 5 seconds for real-time updates

# Timeframes
TIMEFRAME_SIGNAL = "30"      # 30 minutes
TIMEFRAME_4H = "240"         # 4 hours
TIMEFRAME_DAILY = "D"        # Daily

# Number of candles to fetch
CANDLES_30M = 100
CANDLES_4H = 50
CANDLES_DAILY = 30

# =============================================================================
# SERVER SETTINGS
# =============================================================================

API_HOST = "0.0.0.0"
API_PORT = 5001
DEBUG = False  # Disabled to prevent auto-restart and state loss
