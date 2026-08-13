import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class RunEnvironmentTests(unittest.TestCase):
    def test_gpu_compiler_caches_default_to_node_local_root(self):
        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            capture = root / "environment.txt"
            fake_python = bin_dir / "python3.12"
            fake_python.write_text('#!/usr/bin/env bash\nenv > "$ENV_CAPTURE"\n', encoding="utf-8")
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                    "ENV_CAPTURE": str(capture),
                    "RZERO_NODE_CACHE_ROOT": str(root / "cache"),
                    "CUDA_VISIBLE_DEVICES": "0,1",
                    "ROCR_VISIBLE_DEVICES": "0,1,2,3",
                    "HIP_VISIBLE_DEVICES": "0,1,2,3",
                }
            )
            for name in (
                "XDG_CACHE_HOME",
                "TRITON_CACHE_DIR",
                "TORCHINDUCTOR_CACHE_DIR",
                "CUDA_CACHE_PATH",
                "VLLM_CACHE_ROOT",
                "FLASHINFER_WORKSPACE_BASE",
            ):
                env.pop(name, None)

            subprocess.run(
                [str(repo_root / "qwen35/scripts/run.sh"), "--dry-run"],
                cwd=repo_root,
                env=env,
                check=True,
            )
            values = dict(
                line.split("=", 1)
                for line in capture.read_text(encoding="utf-8").splitlines()
                if "=" in line
            )
            expected = {
                "XDG_CACHE_HOME": "xdg",
                "TRITON_CACHE_DIR": "triton",
                "TORCHINDUCTOR_CACHE_DIR": "torchinductor",
                "CUDA_CACHE_PATH": "cuda",
                "VLLM_CACHE_ROOT": "vllm",
                "FLASHINFER_WORKSPACE_BASE": "flashinfer",
            }
            for name, directory in expected.items():
                path = root / "cache" / directory
                self.assertEqual(values[name], str(path))
                self.assertTrue(path.is_dir())
            self.assertEqual(values["VLLM_NO_USAGE_STATS"], "1")
            self.assertEqual(values["CUDA_VISIBLE_DEVICES"], "0,1")
            self.assertNotIn("ROCR_VISIBLE_DEVICES", values)
            self.assertNotIn("HIP_VISIBLE_DEVICES", values)


if __name__ == "__main__":
    unittest.main()
