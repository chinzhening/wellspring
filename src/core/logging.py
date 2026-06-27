import logging
import sys

from core.config import settings


def setup_logging(level: str = settings.log_level):
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
