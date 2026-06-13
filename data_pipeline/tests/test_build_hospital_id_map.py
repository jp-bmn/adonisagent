import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from scripts import build_hospital_id_map


class BuildHospitalIdMapTests(unittest.TestCase):
    def test_extract_rows_from_supported_payload_shapes(self) -> None:
        payload_list = [{"id": "1"}, "bad", {"id": "2"}]
        self.assertEqual(build_hospital_id_map._extract_rows(payload_list), [{"id": "1"}, {"id": "2"}])

        payload_dict = {"hospitals": [{"id": "1"}, {"id": "2"}], "other": []}
        self.assertEqual(build_hospital_id_map._extract_rows(payload_dict), [{"id": "1"}, {"id": "2"}])

        self.assertEqual(build_hospital_id_map._extract_rows({"unknown": []}), [])

    def test_build_id_map_keeps_only_configured_hospitals(self) -> None:
        rows = [
            {"name": " NewYork-Presbyterian ", "id": "nyp-uuid"},
            {"hospital_name": "UMass Memorial", "hospital_id": "umass-uuid"},
            {"name": "Unknown Hospital", "id": "ignore-me"},
            {"name": "", "id": "empty-name"},
        ]

        result = build_hospital_id_map._build_id_map(rows)

        self.assertEqual(
            result,
            {
                "NewYork-Presbyterian": "nyp-uuid",
                "UMass Memorial": "umass-uuid",
            },
        )

    def test_build_id_map_matches_common_aliases(self) -> None:
        rows = [
            {"name": "UAMS Medical Center", "id": "uark-uuid"},
            {"name": "CommonSpirit Health", "id": "commonspirit-uuid"},
            {"name": "Ascension Health", "id": "ascension-uuid"},
            {"name": "New York-Presbyterian", "id": "nyp-uuid"},
        ]

        result = build_hospital_id_map._build_id_map(rows)

        self.assertEqual(result["University of Arkansas"], "uark-uuid")
        self.assertEqual(result["CommonSpirit"], "commonspirit-uuid")
        self.assertEqual(result["Ascension"], "ascension-uuid")
        self.assertEqual(result["NewYork-Presbyterian"], "nyp-uuid")

    def test_collect_unmatched_names_excludes_alias_matches(self) -> None:
        rows = [
            {"name": "UAMS Medical Center", "id": "uark-uuid"},
            {"name": "CommonSpirit Health", "id": "commonspirit-uuid"},
            {"name": "Mystery Regional", "id": "mystery-uuid"},
            {"name": "Mystery Regional", "id": "duplicate"},
        ]

        result = build_hospital_id_map._collect_unmatched_names(rows)

        self.assertEqual(result, ["Mystery Regional"])

    def test_upsert_env_map_replaces_existing_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("FOO=bar\nHOSPITAL_ID_MAP={\"Old\":\"1\"}\n", encoding="utf-8")

            build_hospital_id_map._upsert_env_map(
                env_path,
                {"NewYork-Presbyterian": "new-id"},
            )

            text = env_path.read_text(encoding="utf-8")
            self.assertIn('HOSPITAL_ID_MAP={"NewYork-Presbyterian":"new-id"}', text)
            self.assertNotIn('HOSPITAL_ID_MAP={"Old":"1"}', text)

    @patch("scripts.build_hospital_id_map.requests.get")
    def test_main_unauthorized_has_clear_hint(self, mock_get: Mock) -> None:
        response = Mock()
        response.status_code = 401
        response.url = "https://example.test/api/v1/hospitals?ae_id=abc"
        response.text = '{"detail":"unauthorized"}'
        response.raise_for_status.side_effect = requests.HTTPError("401", response=response)
        mock_get.return_value = response

        argv = [
            "prog",
            "--api-base-url",
            "https://example.test/api/v1",
            "--user-id",
            "abc",
        ]
        with patch("sys.argv", argv):
            with self.assertRaises(SystemExit) as ctx:
                build_hospital_id_map.main()

        message = str(ctx.exception)
        self.assertIn("Unauthorized (401)", message)
        self.assertIn("SIGNALS_ENDPOINT_TOKEN", message)


if __name__ == "__main__":
    unittest.main()
