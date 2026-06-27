import logging

from core.db import SessionLocal, init_db
from core.logging import setup_logging
from pipeline.runner import PipelineRunner
from pipeline.stages import (
    create_stats,
    match_media,
    scrape_media,
    scrape_songs,
)

logger = logging.getLogger(__name__)


def build_pipeline():
    return PipelineRunner(
        [
            ("scrape_songs", scrape_songs.run),
            ("scrape_media", scrape_media.run),
            ("match_media", match_media.run),
            ("create_stats", create_stats.run),
        ]
    )


if __name__ == "__main__":
    # 1. Initialization
    setup_logging()
    init_db()

    # 2. Run pipeline
    with SessionLocal() as db:
        pipeline = build_pipeline()
        pipeline.run(db)

    logger.info("Pipeline completed successfully.")
