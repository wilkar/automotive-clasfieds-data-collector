import asyncio
import logging

from src.config import log_init

log_init.setup_logging()

logger = logging.getLogger(__name__)
from src.main import process


async def main():
    logger.info("Running...")
    await process()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
