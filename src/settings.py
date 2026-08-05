"""
System settings and configurations.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGGING_DIR = BASE_DIR / "LOGGING"

TRACE_FILE = LOGGING_DIR / "trace.jsonl"
METADATA_FILE = LOGGING_DIR / "metadata.json"

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen-2.5-7b-instruct:free")
PARAMETER_SIZE = os.getenv("PARAMETER_SIZE", "7B")
FRAMEWORK = "Custom Multi-Agent (Python)"
POLICY_VERSION = "EC_POLICY_V1"
SCHEMA_VERSION = "1.0"
