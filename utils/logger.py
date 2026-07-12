"""
utils/logger.py
Centralized application logger with rotating file handler and console output.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "devops_dashboard", log_file: str = "logs/app.log",
                  level: str = "INFO") -> logging.Logger:
    """Create and configure a logger with both console and rotating file handlers.

    Args:
        name: Logger name.
        log_file: Path to the log file.
        level: Logging level as a string (e.g. "INFO", "DEBUG").

    Returns:
        A configured Logger instance.
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        # Avoid duplicate handlers on reload
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Filesystem may be read-only (e.g. some container setups) — console-only is fine.
        logger.warning("Could not attach file handler for logging; continuing with console only.")

    return logger


logger = setup_logger()
