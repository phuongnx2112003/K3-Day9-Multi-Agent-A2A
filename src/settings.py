"""
System settings and configurations.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGGING_DIR = BASE_DIR / "logging"

TRACE_FILE = LOGGING_DIR / "trace.jsonl"
METADATA_FILE = LOGGING_DIR / "metadata.json"

MODEL_NAME = "qwen2.5:7b-instruct"  # Model <= 10B parameters
PARAMETER_SIZE = "7B"
FRAMEWORK = "Custom Multi-Agent (Python)"
POLICY_VERSION = "EC_POLICY_V1"
SCHEMA_VERSION = "1.0"
