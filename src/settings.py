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

MODEL_NAME = "gpt-4o-mini"
# OpenAI does not publish an official parameter count for GPT-4o mini.
PARAMETER_SIZE = "Not publicly disclosed"
FRAMEWORK = "Custom Multi-Agent (Python)"
POLICY_VERSION = "EC_POLICY_V1"
SCHEMA_VERSION = "1.0"
