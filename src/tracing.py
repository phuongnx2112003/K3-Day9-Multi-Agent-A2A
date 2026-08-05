"""
Tracing and logging infrastructure.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from src.settings import TRACE_FILE, METADATA_FILE, MODEL_NAME, PARAMETER_SIZE, FRAMEWORK, POLICY_VERSION, SCHEMA_VERSION


def init_trace_file() -> None:
    """Initialize fresh trace.jsonl file."""
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACE_FILE, "w", encoding="utf-8") as f:
        pass


def log_event(
    run_id: str,
    trace_id: str,
    case_id: str,
    event: str,
    agent: str,
    status: str = "success",
    duration_ms: int = 0,
    input_refs: Optional[list] = None,
    output_summary: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Log an event to trace.jsonl."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "trace_id": trace_id,
        "case_id": case_id,
        "event": event,
        "agent": agent,
        "status": status,
        "duration_ms": duration_ms,
        "input_refs": input_refs or [],
        "output_summary": output_summary or {},
        "error": error,
    }
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_metadata(commit_sha: str = "main") -> None:
    """Write system metadata.json."""
    metadata = {
        "model_name": MODEL_NAME,
        "parameter_size": PARAMETER_SIZE,
        "framework": FRAMEWORK,
        "policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
    }
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
