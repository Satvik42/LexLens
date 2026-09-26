"""Logging setup. Application code must never log raw document text or secrets."""

import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Third-party libraries can be verbose; keep the signal in our own logs.
    for noisy in ("httpx", "httpcore", "google", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
