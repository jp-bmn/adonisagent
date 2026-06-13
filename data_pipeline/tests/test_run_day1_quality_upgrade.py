import unittest

from adonis_data.models import RawSignal
from scripts import run_day1_collection


class RunDay1QualityUpgradeTests(unittest.TestCase):
    def test_low_information_reason_flags_sparse_signal(self) -> None:
        signal = RawSignal(
            hospital="Ascension",
            title="RCM update",
            source="Example",
            url="https://example.com/a",
            published_at="2026-06-01",
            matched_topics=["revenue_cycle"],
            excerpt="Short summary only",
        )

        reason = run_day1_collection._low_information_reason(signal)
        self.assertEqual(reason, "low_information_signal")

    def test_low_information_reason_keeps_informative_signal(self) -> None:
        signal = RawSignal(
            hospital="Ascension",
            title="Ascension names new vice president of revenue cycle operations",
            source="Example",
            url="https://example.com/b",
            published_at="2026-06-01",
            matched_topics=["leadership", "revenue_cycle"],
            excerpt=(
                "Ascension appointed a new vice president for revenue cycle and outlined "
                "a multi-hospital claims optimization initiative for fiscal 2026."
            ),
        )

        reason = run_day1_collection._low_information_reason(signal)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
