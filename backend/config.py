"""
CryptoFastSignals - Configuration v4.0.0
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
MIN_LEVERAGE = 50           # Minimum 50x leverage required
HISTORY_RETENTION_HOURS = 72 # 3 days

# Smart Exit Settings
STOP_LOSS_PERCENT = 0.01   # 1%
TAKE_PROFIT_PERCENT = 0.02  # 2% (Default for Trending)
PARTIAL_TP_PERCENT = 0.02    # 2% (Target 1 - Close 50% and move SL to Entry)
TRAILING_STOP_TRIGGER = 0.03 # 3% (Activate Trailing Stop)
TRAILING_STOP_DISTANCE = 0.01 # 1% (SL follows price at 1% distance)
TARGET_SNIPER_6 = 0.06       # 6% Super Target
SNIPER_FORCE_TARGET = 0.06   # Force 6% target in sniper mode
SNIPER_DECOUPLING_THRESHOLD = 0.40 # Minimum decoupling for ranging sniper
SNIPER_BEST_SCORE_THRESHOLD = 70  # Lowered for demo (Standard: 85)

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
MIN_SCORE_TO_SAVE = 65          # Minimum score to save signal

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

# =============================================================================
# MACHINE LEARNING SETTINGS
# =============================================================================

ML_ENABLED = True
ML_PROBABILITY_THRESHOLD = 0.25  # 25% minimum probability (Training Mode)
ML_MIN_SAMPLES = 100             # Minimum samples required to train model
ML_AUTO_RETRAIN_INTERVAL = 30    # Retrain every 30 new finalized signals (more aggressive)
ML_MODEL_PATH = "services/ml_model.pkl"
ML_METRICS_PATH = "services/ml_metrics.json"
ML_HYBRID_SCORE_WEIGHT = 0.4     # 40% ML weight (lowered from 60%)

# =============================================================================
# BTC REGIME SETTINGS
# =============================================================================

# Regime Detection Thresholds
BTC_BB_WIDTH_RANGING = 0.02         # BB width < 2% = ranging
BTC_ATR_PCT_RANGING = 0.005         # ATR/Price < 0.5% = low volatility
BTC_TREND_EMA_DIST = 0.005          # EMA distance > 0.5% = trending
BTC_BREAKOUT_VOLUME = 2.0           # Volume > 2x average = potential breakout
BTC_BREAKOUT_ATR_EXPANSION = 1.5    # ATR expanding 50% = volatility spike

# Dynamic TP/SL by Regime
TP_RANGING = 0.01                   # 1% TP for ranging market
SL_RANGING = 0.005                  # 0.5% SL for ranging market
TP_TRENDING = 0.02                  # 2% TP for trending market (default)
SL_TRENDING = 0.01                  # 1% SL for trending market (default)
TP_BREAKOUT = 0.03                  # 3% TP for breakout
SL_BREAKOUT = 0.015                 # 1.5% SL for breakout

# Decoupling Score Bonus (added to signal score when alt is decoupled in ranging)
DECOUPLING_SCORE_BONUS = 15         # +15 points for decoupled alts in ranging regime

# =============================================================================
# LLM INTELLIGENCE SETTINGS (Gemini)
# =============================================================================

LLM_ENABLED = True                       # Master switch for LLM features
LLM_MODEL = "gemini-2.0-flash"           # Free tier model (updated name)
LLM_VALIDATE_SIGNALS = True              # Validate signals before emitting
LLM_OPTIMIZE_TP = True                   # Suggest optimized TPs
LLM_MONITOR_EXITS = True                 # Analyze exit opportunities
LLM_CACHE_TTL_SECONDS = 300              # Cache TTL: 5 minutes
LLM_MIN_CONFIDENCE = 0.6                 # Minimum confidence to approve signal
