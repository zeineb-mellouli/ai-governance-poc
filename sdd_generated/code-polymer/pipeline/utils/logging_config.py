"""
pipeline/utils/logging_config.py
---------------------------------
Shared file-based logging factory for all Polymer Pricing ETL scripts.

Constitution IV: Use Python logging module with FileHandler throughout.
Never use bare print() for operational messages.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str, log_dir: str) -> logging.Logger:
    """Return a configured Logger that writes to a dated log file.

    Creates ``log_dir`` if it does not exist. Attaches a single
    ``FileHandler`` writing to ``{log_dir}/PipelineRun_YYYYMMDD.log``
    at INFO level. No StreamHandler is added — all output goes to the
    file (Constitution IV).

    Args:
        name:    Logger name (used as the ``%(name)s`` field in log records).
        log_dir: Directory where the log file is written.

    Returns:
        Configured :class:`logging.Logger`.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    log_filename = f"PipelineRun_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls (e.g., in tests)
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Prevent double-logging to root logger

    return logger
