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
from sqlalchemy.sql import select

# Add src to path to allow importing project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import necessary project components
from src.config.database import get_db_settings  # noqa: E402
from src.entities.value_objects.calibration_type import CalibrationType  # noqa: E402
from src.infrastructure.orm_models import (
    CalibrationORM,
    TagORM,
    CalibrationTagAssociationORM,
)  # noqa: E402

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
            current_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
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

            # --- Tag Seeding ---
            tag_names = ["foo", "bar", "baz"]
            logger.info(f"Ensuring tags exist: {tag_names}")
            tag_orm_objects = {}

            # Check existing tags
            stmt_tags = select(TagORM).where(TagORM.name.in_(tag_names))
            result_tags = await session.execute(stmt_tags)
            existing_tags = result_tags.scalars().all()
            for tag in existing_tags:
                tag_orm_objects[tag.name] = tag

            # Create missing tags
            new_tags_to_add = []
            for name in tag_names:
                if name not in tag_orm_objects:
                    logger.info(f"Creating tag: {name}")
                    new_tag = TagORM(id=uuid4(), name=name)
                    new_tags_to_add.append(new_tag)
                    tag_orm_objects[name] = new_tag

            if new_tags_to_add:
                session.add_all(new_tags_to_add)
                await session.commit()
                logger.info(f"Added {len(new_tags_to_add)} new tags.")
            else:
                logger.info("All required tags already existed.")

            # --- Association Seeding ---
            logger.info("Creating tag associations for calibrations...")
            associations_to_add = []
            tag_list = list(tag_orm_objects.values()) # Get list of TagORM objects
            base_association_time = datetime.now(UTC) # Get base time before loop

            if not tag_list:
                logger.warning("No tags available to create associations.")
                return

            association_counter = 0 # Initialize counter for archiving
            for i, cal_orm in enumerate(orm_objects):
                # Calculate association time: subtract 0, 1, or 2 minutes cyclically
                minute_offset = i % 3
                association_time = base_association_time - timedelta(minutes=minute_offset)

                # Determine how many tags to assign (1, 2, or 3 cyclically)
                num_tags_to_assign = (i % 3) + 1
                tags_to_assign_this_round = tag_list[:num_tags_to_assign]

                logger.debug(
                    f"Associating calibration {cal_orm.id} with {num_tags_to_assign} tags at {association_time}"
                )

                # Create an association for each tag to be assigned
                for tag_to_assign in tags_to_assign_this_round:
                    association_counter += 1 # Increment counter
                    archive_time = None
                    log_msg_suffix = ""
                    # Archive every third association
                    if association_counter % 3 == 0:
                        archive_time = association_time # Set archived_at to the creation time
                        log_msg_suffix = " (ARCHIVED)"

                    logger.debug(f"  - Tag: '{tag_to_assign.name}'{log_msg_suffix}")
                    assoc = CalibrationTagAssociationORM(
                        id=uuid4(),
                        calibration_id=cal_orm.id,
                        tag_id=tag_to_assign.id,
                        created_at=association_time, # Use same time for all tags on this cal
                        archived_at=archive_time # Set if applicable
                    )
                    associations_to_add.append(assoc)

            if associations_to_add:
                session.add_all(associations_to_add)
                await session.commit()
                logger.success(f"Successfully created {len(associations_to_add)} tag associations.")
            else:
                logger.warning("No tag associations created.")

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
