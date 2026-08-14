import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class VerlTextOnlyTests(unittest.TestCase):
    def test_external_lib_disables_only_multimodal_processor(self):
        config_module = types.ModuleType("verl.workers.config.model")
        sentinel = object()
        config_module.hf_processor = lambda *_args, **_kwargs: sentinel

        module_path = Path(__file__).resolve().parents[1] / "rzero/verl_text_only.py"
        spec = importlib.util.spec_from_file_location("rzero_verl_text_only_test", module_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules,
            {
                "verl": types.ModuleType("verl"),
                "verl.workers": types.ModuleType("verl.workers"),
                "verl.workers.config": types.ModuleType("verl.workers.config"),
                "verl.workers.config.model": config_module,
            },
        ):
            spec.loader.exec_module(module)

        self.assertIsNone(config_module.hf_processor("/model"))


if __name__ == "__main__":
    unittest.main()
