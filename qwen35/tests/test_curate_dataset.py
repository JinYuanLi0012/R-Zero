import unittest

from qwen35.rzero.curate_dataset import repeat_for_integration


class CurateDatasetTests(unittest.TestCase):
    def test_integration_repeat_is_deterministic_and_preserves_sources(self):
        records = [
            {"prompt": "a", "extra_info": {"index": 0}},
            {"prompt": "b", "extra_info": {"index": 1}},
        ]
        expanded = repeat_for_integration(records, 5)

        self.assertEqual([row["prompt"] for row in expanded], ["a", "b", "a", "b", "a"])
        self.assertEqual(len(records), 2)
        self.assertEqual(expanded[2]["extra_info"]["integration_source_index"], 0)
        self.assertEqual(expanded[4]["extra_info"]["integration_repeat"], 2)

    def test_full_batch_is_not_modified(self):
        records = [{"prompt": str(index)} for index in range(4)]
        self.assertIs(repeat_for_integration(records, 4), records)

    def test_minimum_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            repeat_for_integration([{"prompt": "a"}], 0)


if __name__ == "__main__":
    unittest.main()
