import copy
import unittest
from pathlib import Path

from qwen35.rzero.config import ConfigError, load_config, validate_config


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"


class ConfigTests(unittest.TestCase):
    def test_formal_profile(self):
        config = load_config(CONFIG)
        self.assertEqual(config["model"]["id"], "Qwen/Qwen3.5-4B-Base")
        self.assertEqual(config["generation"]["shards"] * config["generation"]["samples_per_shard"], 8000)

    def test_rejects_candidate_scale_drift(self):
        config = load_config(CONFIG)
        config = copy.deepcopy({key: value for key, value in config.items() if not key.startswith("_")})
        config["generation"]["samples_per_shard"] = 1000
        with self.assertRaises(ConfigError):
            validate_config(config)

    def test_rejects_released_algorithm_drift(self):
        config = load_config(CONFIG)
        config = copy.deepcopy({key: value for key, value in config.items() if not key.startswith("_")})
        config["algorithm"]["candidate_vote_samples"] = 10
        with self.assertRaises(ConfigError):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()
