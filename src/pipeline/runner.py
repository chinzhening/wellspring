import logging

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(self, stages):
        self.stages = stages

    def run(self, db, **args):
        for name, stage_fn in self.stages:
            try:
                logger.info(f"Running stage: {name}")
                stage_fn(db, **args)

            except Exception:
                logger.exception(f"Stage failed: {name}")
                raise
