import json
import logging
from datetime import datetime, timezone
from typing import Any


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level.upper(), format="%(message)s")


def log_event(logger: logging.Logger, level: str, event_name: str, message: str, **context: Any) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "event_name": event_name,
        "message": message,
        "context": context,
    }
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(json.dumps(payload, default=str))
