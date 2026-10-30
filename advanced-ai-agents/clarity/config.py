"""
Clarity — Configuration
"""
import os

# Default LLM provider
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# Risk thresholds
RISK_HIGH_THRESHOLD = 0.7
RISK_MEDIUM_THRESHOLD = 0.4

# Output formatting
MAX_CLAUSE_LENGTH = 2000
