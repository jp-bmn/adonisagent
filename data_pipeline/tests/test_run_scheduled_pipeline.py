import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import run_scheduled_pipeline


class ScheduledPipelineTests(unittest.TestCase):
    def test_run_with_retries_succeeds_after_transient_failure(self) -> None:
        state = {"calls": 0}

        def flaky_task() -> None:
            state["calls"] += 1
            if state["calls"] < 2:
                raise RuntimeError("transient")

        with patch("scripts.run_scheduled_pipeline.time.sleep") as mock_sleep:
            result = run_scheduled_pipeline._run_with_retries(
                task=flaky_task,
                attempts=3,
                backoff_seconds=1,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.attempts, 2)
        mock_sleep.assert_called_once_with(1)

    def test_acquire_lock_blocks_when_fresh_lock_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "scheduler.lock"
            fresh_payload = {
                "pid": 111,
                "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            lock_path.write_text(__import__("json").dumps(fresh_payload), encoding="utf-8")

            with self.assertRaises(run_scheduled_pipeline.LockAcquisitionError):
                run_scheduled_pipeline._acquire_lock(lock_path, stale_lock_minutes=10)

    def test_acquire_lock_replaces_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "scheduler.lock"
            stale_payload = {
                "pid": 111,
                "acquired_at_utc": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
            }
            lock_path.write_text(__import__("json").dumps(stale_payload), encoding="utf-8")

            run_scheduled_pipeline._acquire_lock(lock_path, stale_lock_minutes=60)
            payload = run_scheduled_pipeline._read_json(lock_path)
            self.assertIn("pid", payload)
            self.assertIn("acquired_at_utc", payload)

            run_scheduled_pipeline._release_lock(lock_path)
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
