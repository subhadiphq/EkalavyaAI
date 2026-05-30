"""EkalavyaAI — Structured Logging Setup"""
import logging
import sys


def setup_logging():
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Quiet noisy libs
    for lib in ("httpx", "httpcore", "openai", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)
