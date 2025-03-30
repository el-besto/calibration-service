#!/usr/bin/env python

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import sqlalchemy
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add src to path to allow importing project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import necessary project components
from src.config.database import get_db_settings  # noqa: E402
from src.entities.value_objects.calibration_type import CalibrationType  # noqa: E402
from src.infrastructure.orm_models import CalibrationORM  # noqa: E402

# Configure logger for the script
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")


async def seed_data(db_url: str, data_file: Path, clear_existing: bool = True):
    """Seeds the database with calibration data."""
    logger.info(
        f"Starting database seeding process using URL: {db_url[: db_url.find('@')] + '@...' if '@' in db_url else db_url}"
    )
    logger.info(f"Loading data from: {data_file}")

    engine = create_async_engine(db_url, echo=False)
    async_session_factory = sessionmaker(  # pyright: ignore [reportCallIssue]
        bind=engine,  # pyright: ignore [reportArgumentType]
        class_=AsyncSession,
        expire_on_commit=False,  # pyright: ignore [reportArgumentType]
    )

    try:
        with open(data_file) as f:  # noqa: PTH123
            sample_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Data file not found: {data_file}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {data_file}")
        return

    async with async_session_factory() as session:  # pyright: ignore [reportGeneralTypeIssues]
        try:
            if clear_existing:
                logger.warning("Clearing existing calibration data...")
                stmt = sqlalchemy.delete(CalibrationORM)
                await session.execute(stmt)
                logger.info("Existing calibration data cleared.")

            logger.info(f"Seeding {len(sample_data)} calibration records...")
            current_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            orm_objects = []
            for i, item in enumerate(sample_data):
                try:
                    cal_type = CalibrationType(item["calibration_type"])
                    orm_objects.append(
                        CalibrationORM(
                            id=uuid4(),
                            value=float(item["value"]),
                            type=cal_type,
                            timestamp=current_time + timedelta(hours=i),
                            username=item["username"],
                        )
                    )
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        f"Skipping invalid data item {i + 1}: {item}. Error: {e}"
                    )
                    continue

            if not orm_objects:
                logger.warning("No valid calibration objects created from sample data.")
                return

            session.add_all(orm_objects)
            await session.commit()
            logger.success(
                f"Successfully seeded {len(orm_objects)} calibration records."
            )

        except Exception as e:
            logger.error(f"An error occurred during seeding: {e}")
            await session.rollback()

    await engine.dispose()


async def main():
    db_settings = get_db_settings()
    data_path = project_root / "scripts" / "sample_data" / "sample_calibrations.json"
    await seed_data(db_settings.database_url, data_path, clear_existing=True)


if __name__ == "__main__":
    asyncio.run(main())
