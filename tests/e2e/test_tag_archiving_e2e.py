import asyncio
import uuid
from datetime import UTC, datetime

import httpx
import pytest

from config.logger import log_test_step

# --- Configuration ---
BASE_URL = "http://localhost:8000"
# How long to wait between adding and removing a tag (adjust if needed)
WAIT_SECONDS = 2


@pytest.mark.asyncio
async def test_tag_archiving_with_timestamp():  # noqa: PLR0915
    """
    Tests retrieving historical tag associations using the timestamp parameter.
    - Creates a calibration.
    - Adds two tags (tag_A, tag_B).
    - Records timestamp (t1).
    - Waits.
    - Removes tag_B.
    - Records timestamp (t2).
    - Queries tags at t1, expects [tag_A, tag_B].
    - Queries tags at t2 (or now), expects [tag_A].
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        created_calibration_id = None
        tag_a_name = f"e2e_tag_A_{uuid.uuid4()}"
        tag_b_name = f"e2e_tag_B_{uuid.uuid4()}"

        try:
            # --- Setup: Create Calibration ---
            log_test_step("\n--- Setup: Creating Calibration ---")
            calibration_payload = {
                "type": "gain",
                "value": 1.1,
                "timestamp": datetime.now(UTC).isoformat(),
                "username": "e2e_archiving_tester",
            }
            response = await client.post("/calibrations", json=calibration_payload)
            assert response.status_code == 201, (
                f"Failed to create calibration: {response.text}"
            )
            created_calibration_id = response.json()["calibration_id"]
            log_test_step(f"Created Calibration ID: {created_calibration_id}")

            # --- Setup: Add Tag A ---
            log_test_step(f"--- Setup: Adding Tag A: {tag_a_name} ---")
            tag_payload_a = {"tag": tag_a_name}
            response = await client.post(
                f"/calibrations/{created_calibration_id}/tags", json=tag_payload_a
            )
            assert response.status_code == 200, f"Failed to add tag A: {response.text}"
            log_test_step("Added Tag A successfully.")

            # --- Setup: Add Tag B ---
            log_test_step(f"--- Setup: Adding Tag B: {tag_b_name} ---")
            tag_payload_b = {"tag": tag_b_name}
            response = await client.post(
                f"/calibrations/{created_calibration_id}/tags", json=tag_payload_b
            )
            assert response.status_code == 200, f"Failed to add tag B: {response.text}"
            log_test_step("Added Tag B successfully.")

            # --- Record Time Before Removal ---
            # Add a small buffer before to ensure query time is after additions
            await asyncio.sleep(0.5)
            timestamp_before_removal = datetime.now(UTC)
            # Format for query parameter (URL encoding might handle '+', but safer this way)
            timestamp_query_val_before = (
                timestamp_before_removal.isoformat().replace("+", "%2B") + "Z"
            )
            log_test_step(
                f"Timestamp before removal (t1): {timestamp_query_val_before}"
            )

            # --- Wait ---
            log_test_step(f"--- Waiting for {WAIT_SECONDS} seconds ---")
            await asyncio.sleep(WAIT_SECONDS)

            # --- Action: Remove Tag B ---
            log_test_step(f"--- Action: Removing Tag B: {tag_b_name} ---")
            response = await client.delete(
                f"/calibrations/{created_calibration_id}/tags/{tag_b_name}"
            )
            assert response.status_code == 200, (
                f"Failed to remove tag B: {response.text}"
            )
            log_test_step("Removed Tag B successfully.")

            # --- Record Time After Removal ---
            # Add a small buffer to ensure query time is after removal
            await asyncio.sleep(0.5)
            timestamp_after_removal = datetime.now(UTC)
            timestamp_query_val_after = (
                timestamp_after_removal.isoformat().replace("+", "%2B") + "Z"
            )
            log_test_step(f"Timestamp after removal (t2): {timestamp_query_val_after}")

            # --- Test 1: Query Tags at t1 (Before Removal) ---
            log_test_step(
                f"\n--- Test 1: GET tags at t1: {timestamp_query_val_before} ---"
            )
            response = await client.get(
                f"/calibrations/{created_calibration_id}/tags?timestamp={timestamp_query_val_before}"
            )
            log_test_step(
                f"GET /calibrations/.../tags?timestamp=t1 status: {response.status_code}"
            )
            assert response.status_code == 200, f"Failed query at t1: {response.text}"
            tags_at_t1 = response.json()
            log_test_step(f"Tags found at t1: {tags_at_t1}")
            assert isinstance(tags_at_t1, list)
            assert set(tags_at_t1) == {tag_a_name, tag_b_name}, (
                "Should find both tags at t1"
            )
            log_test_step("Check at t1 PASSED.")

            # --- Test 2: Query Tags at t2 (After Removal) ---
            log_test_step(
                f"\n--- Test 2: GET tags at t2: {timestamp_query_val_after} ---"
            )
            response = await client.get(
                f"/calibrations/{created_calibration_id}/tags?timestamp={timestamp_query_val_after}"
            )
            log_test_step(
                f"GET /calibrations/.../tags?timestamp=t2 status: {response.status_code}"
            )
            assert response.status_code == 200, f"Failed query at t2: {response.text}"
            tags_at_t2 = response.json()
            log_test_step(f"Tags found at t2: {tags_at_t2}")
            assert isinstance(tags_at_t2, list)
            assert set(tags_at_t2) == {tag_a_name}, "Should only find tag_A at t2"
            log_test_step("Check at t2 PASSED.")

            # --- Test 3: Query Tags Now (Should be same as t2) ---
            log_test_step("\n--- Test 3: GET tags now (no timestamp parameter) ---")
            response = await client.get(f"/calibrations/{created_calibration_id}/tags")
            log_test_step(
                f"GET /calibrations/.../tags (now) status: {response.status_code}"
            )
            assert response.status_code == 200, f"Failed query now: {response.text}"
            tags_now = response.json()
            log_test_step(f"Tags found now: {tags_now}")
            assert isinstance(tags_now, list)
            assert set(tags_now) == {tag_a_name}, "Should only find tag_A now"
            log_test_step("Check now PASSED.")

            log_test_step("\n--- E2E Tag Archiving Test Completed Successfully ---")

        finally:
            # --- Cleanup (Optional but Recommended) ---
            # Attempt to remove the other tag as well, ignore errors if it fails
            if created_calibration_id:
                log_test_step(f"\n--- Cleanup: Removing remaining tag {tag_a_name} ---")
                try:
                    await client.delete(
                        f"/calibrations/{created_calibration_id}/tags/{tag_a_name}"
                    )
                    log_test_step("Cleanup successful.")
                except Exception as e:
                    log_test_step(f"Cleanup failed (ignoring): {e}")
