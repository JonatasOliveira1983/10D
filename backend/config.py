"""
CryptoFastSignals - Configuration
"""

# =============================================================================
# INDICATOR SETTINGS
# =============================================================================

# SMA Settings
SMA_FAST_PERIOD = 8
SMA_SLOW_PERIOD = 21

# Pivot Point S. Trend Settings
PIVOT_PERIOD = 1
ATR_FACTOR = 2
ATR_PERIOD = 10

# Volume Settings
VOLUME_THRESHOLD = 1.2  # 1.2x average volume (was 1.5x - too restrictive)
VOLUME_LOOKBACK = 20    # Last 20 candles for average

# RSI Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 35       # RSI below this = oversold (was 30)
RSI_OVERBOUGHT = 65     # RSI above this = overbought (was 70)

# Pullback Settings
PULLBACK_THRESHOLD = 0.005  # 0.5% - price within this distance from SMA (was 0.3%)

# =============================================================================
# S/R SETTINGS
# =============================================================================

SR_PROXIMITY_THRESHOLD = 0.005  # 0.5% distance
SR_LOOKBACK_DAYS = 20           # 20 days for high/low

# =============================================================================
# TRADING SETTINGS
# =============================================================================

STOP_LOSS_PERCENT = 0.01   # 1%
TAKE_PROFIT_PERCENT = 0.02  # 2%
MIN_LEVERAGE = 50           # Minimum 50x leverage required

# Pair settings
PAIR_LIMIT = 100            # Monitor top 100 pairs by volume
EXCLUDED_PAIRS = [          # Pairs to exclude from monitoring
    "BTCUSDT",              # BTC leads the market, we follow it, not trade it
]

# =============================================================================
# SCORING SETTINGS
# =============================================================================

# Base scores for signal types
SCORE_SMA_CROSSOVER = 30        # SMA 8 crosses SMA 21
SCORE_TREND_PULLBACK = 25       # Pullback to SMA during trend
SCORE_RSI_EXTREME = 20          # RSI oversold/overbought reversal

# Confirmation bonuses
SCORE_VOLUME_CONFIRMED = 25
SCORE_PIVOT_CONFIRMED = 20
SCORE_SR_ALIGNED = 25
SCORE_SR_MISALIGNED = -15

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
