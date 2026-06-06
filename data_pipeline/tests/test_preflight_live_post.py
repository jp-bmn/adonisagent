import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from scripts import preflight_live_post


class PreflightLivePostTests(unittest.TestCase):
    def test_parse_hospital_id_map_handles_invalid_and_valid_json(self) -> None:
        self.assertEqual(preflight_live_post._parse_hospital_id_map(""), {})
        self.assertEqual(preflight_live_post._parse_hospital_id_map("not-json"), {})
        self.assertEqual(preflight_live_post._parse_hospital_id_map('["a"]'), {})
        self.assertEqual(
            preflight_live_post._parse_hospital_id_map('{"A":"1","B":"2"}'),
            {"A": "1", "B": "2"},
        )

    def test_upsert_env_values_missing_only_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("POST_SIGNALS_ENABLED=true\n", encoding="utf-8")

            changed = preflight_live_post._upsert_env_values_missing_only(
                env_path,
                {
                    "POST_SIGNALS_ENABLED": "false",
                    "OUTBOX_ENABLED": "true",
                },
            )

            text = env_path.read_text(encoding="utf-8")
            self.assertEqual(changed, ["OUTBOX_ENABLED"])
            self.assertIn("POST_SIGNALS_ENABLED=true", text)
            self.assertIn("OUTBOX_ENABLED=true", text)

    @patch("scripts.preflight_live_post.requests.options")
    def test_check_endpoint_reachable_passes_on_405(self, mock_options: Mock) -> None:
        response = Mock(status_code=405)
        mock_options.return_value = response

        result = preflight_live_post._check_endpoint_reachable(
            endpoint_url="https://example.test/api/v1/signals/batch",
            token="token123",
            timeout_seconds=10,
        )

        self.assertEqual(result.level, "PASS")
        self.assertEqual(result.name, "endpoint_reachability")
        self.assertIn("status=405", result.detail)

    @patch("scripts.preflight_live_post.requests.options")
    def test_check_endpoint_reachable_fails_on_network_error(self, mock_options: Mock) -> None:
        mock_options.side_effect = requests.RequestException("network down")

        result = preflight_live_post._check_endpoint_reachable(
            endpoint_url="https://example.test/api/v1/signals/batch",
            token="",
            timeout_seconds=10,
        )

        self.assertEqual(result.level, "FAIL")
        self.assertIn("Could not reach endpoint", result.detail)

    @patch("scripts.preflight_live_post.load_settings")
    def test_run_returns_blocked_when_hospital_coverage_incomplete(self, mock_load_settings: Mock) -> None:
        mock_load_settings.return_value = SimpleNamespace(
            post_signals_enabled=True,
            quality_mode="balanced",
            signals_endpoint_url="https://example.test/api/v1/signals/batch",
            signals_endpoint_token="abc123456",
            outbox_enabled=True,
            request_timeout_seconds=20,
        )

        with patch.dict(os.environ, {"HOSPITAL_ID_MAP": '{"NewYork-Presbyterian":"1"}'}, clear=False):
            exit_code = preflight_live_post.run(check_endpoint=False)

        self.assertEqual(exit_code, 2)

    @patch("scripts.preflight_live_post.load_settings")
    def test_run_returns_ready_when_all_checks_pass(self, mock_load_settings: Mock) -> None:
        mock_load_settings.return_value = SimpleNamespace(
            post_signals_enabled=True,
            quality_mode="balanced",
            signals_endpoint_url="https://example.test/api/v1/signals/batch",
            signals_endpoint_token="abc123456",
            outbox_enabled=True,
            request_timeout_seconds=20,
        )

        full_map = {
            "NewYork-Presbyterian": "id-1",
            "UMass Memorial": "id-2",
            "Ascension": "id-3",
            "University of Arkansas": "id-4",
            "CommonSpirit": "id-5",
        }

        with patch.dict(os.environ, {"HOSPITAL_ID_MAP": str(full_map).replace("'", '"')}, clear=False):
            exit_code = preflight_live_post.run(check_endpoint=False)

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
