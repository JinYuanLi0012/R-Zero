import csv
import json
import os
from pathlib import Path
import sys
import unittest
import threading
from unittest.mock import patch
from evaluation import evaluate_models as batch
from evaluation.tests import test_evaluate_models

class NonmathBatchTest(unittest.TestCase):
    setUp = test_evaluate_models.EvaluateModelsTest.setUp
    def emit_nonmath(self, command, cwd, env, stdout, stderr):
        dataset = Path(command[1]).stem.removeprefix('eval_')
        self.assertIn(dataset, batch.NONMATH_DATASETS)
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'], '0,1,2,3')
        self.assertEqual(env['EVAL_TENSOR_PARALLEL_SIZE'], '4')
        self.assertTrue(Path(env['TORCHINDUCTOR_CACHE_DIR']).is_dir())
        model = command[command.index('--model_path') + 1]
        Path(env['FINAL_RESULTS_FILE']).write_text(json.dumps(dict(model=model, dataset=dataset,
            accuracy=10 + 10 * batch.NONMATH_DATASETS.index(dataset)), indent=2))
        return 0

    def test_nonmath_outputs_copies_and_summary_only(self):
        with patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--batch-dir', str(self.output)] + self.paths[:2]), patch.object(batch.subprocess, 'call', side_effect=self.emit_nonmath) as call:
            batch.main()
            self.assertEqual(call.call_count, 6)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertIsNone(manifest['judge'])
        with (self.output / 'summary.csv').open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]['ave_nonmath'], '20.0')
        self.assertNotIn('math', rows[0])
        for item in manifest['models']:
            copy = Path(item['checkpoint_results_dir'])
            self.assertEqual((copy / 'final_results.jsonl').read_bytes(), (self.output / item['results_file']).read_bytes())
        with patch.object(sys, 'argv', ['runner', '--summary-only', str(self.output)]), patch.object(batch.subprocess, 'call') as call:
            batch.main()
            call.assert_not_called()

    def test_nonmath_failure_stops_later_models(self):
        def emit(*args, **kwargs):
            if Path(args[0][1]).stem == 'eval_bbeh':
                return 1
            return self.emit_nonmath(*args, **kwargs)
        with patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--batch-dir', str(self.output)] + self.paths), patch.object(batch.subprocess, 'call', side_effect=emit) as call:
            with self.assertRaises(SystemExit):
                batch.main()
            self.assertEqual(call.call_count, 2)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        rows = batch.summarize(self.output, manifest)
        self.assertEqual(rows[0][2], 'failed')
        self.assertEqual(rows[0][-3], '')
        self.assertEqual(rows[1][2], 'pending')
        self.assertNotIn('checkpoint_results_dir', manifest['models'][0])

    def test_nonmath_mismatched_score_rejected(self):
        def emit(command, cwd, env, **kwargs):
            Path(env['FINAL_RESULTS_FILE']).write_text(json.dumps(dict(model='wrong', dataset='supergpqa', accuracy=90)))
            return 0
        with patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--batch-dir', str(self.output)] + self.paths[:1]), patch.object(batch.subprocess, 'call', side_effect=emit):
            with self.assertRaises(SystemExit):
                batch.main()
        self.assertFalse((self.output / '001/final_results.jsonl').exists())

    def test_three_gpus_run_concurrently_without_tensor_parallel_three(self):
        barrier = threading.Barrier(3, timeout=5)
        seen = {}
        def emit(command, cwd, env, stdout, stderr):
            dataset = Path(command[1]).stem.removeprefix('eval_')
            self.assertEqual(env['EVAL_TENSOR_PARALLEL_SIZE'], '1')
            gpu = env['CUDA_VISIBLE_DEVICES']
            self.assertEqual(gpu, str(1 + batch.NONMATH_DATASETS.index(dataset)))
            self.assertNotIn('VLLM_PORT', env)
            seen[dataset] = env['TORCHINDUCTOR_CACHE_DIR']
            barrier.wait()  # Fails if the three tasks were launched sequentially.
            model = command[command.index('--model_path') + 1]
            Path(env['FINAL_RESULTS_FILE']).write_text(json.dumps(dict(
                model=model, dataset=dataset, accuracy=50)))
            return 0
        with patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--gpu-ids', '1,2,3',
                '--batch-dir', str(self.output)] + self.paths[:1]), \
             patch.object(batch.subprocess, 'call', side_effect=emit) as call:
            batch.main()
            self.assertEqual(call.call_count, 3)
        self.assertEqual(len(set(seen.values())), 3)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        rows = batch.summarize(self.output, manifest)
        self.assertEqual(rows[0][2], 'complete')
        self.assertEqual(rows[0][-3], 50)
        self.assertEqual(len((self.output / '001/final_results.jsonl').read_text().splitlines()), 3)

    def test_three_gpu_failure_preserves_other_scores_and_stops_next_model(self):
        barrier = threading.Barrier(3, timeout=5)
        def emit(command, cwd, env, **kwargs):
            dataset = Path(command[1]).stem.removeprefix('eval_')
            barrier.wait()
            if dataset == 'bbeh':
                return 1
            model = command[command.index('--model_path') + 1]
            Path(env['FINAL_RESULTS_FILE']).write_text(json.dumps(dict(
                model=model, dataset=dataset, accuracy=50)))
            return 0
        with patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--gpu-ids', '1,2,3',
                '--batch-dir', str(self.output)] + self.paths[:2]), \
             patch.object(batch.subprocess, 'call', side_effect=emit) as call:
            with self.assertRaises(SystemExit):
                batch.main()
            self.assertEqual(call.call_count, 3)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        rows = batch.summarize(self.output, manifest)
        self.assertEqual(rows[0][2], 'failed')
        self.assertEqual(rows[0][-3], '')
        self.assertEqual(rows[1][2], 'pending')
        self.assertNotIn('checkpoint_results_dir', manifest['models'][0])
        self.assertEqual(len((self.output / '001/final_results.jsonl').read_text().splitlines()), 2)

    def test_three_gpu_port_base_reaches_each_benchmark_process(self):
        seen = {}
        def emit(command, cwd, env, **kwargs):
            dataset = Path(command[1]).stem.removeprefix('eval_')
            seen[dataset] = env['VLLM_PORT']
            model = command[command.index('--model_path') + 1]
            Path(env['FINAL_RESULTS_FILE']).write_text(json.dumps(dict(
                model=model, dataset=dataset, accuracy=50)))
            return 0
        with patch.dict(os.environ, {'RZERO_NONMATH_VLLM_PORT_BASE': '31000', 'VLLM_PORT': '12345'}), \
             patch.object(sys, 'argv', ['runner', '--suite', 'nonmath', '--gpu-ids', '1,2,3',
                '--batch-dir', str(self.output)] + self.paths[:1]), \
             patch.object(batch.subprocess, 'call', side_effect=emit):
            batch.main()
            self.assertEqual(os.environ['VLLM_PORT'], '12345')
        self.assertEqual(seen, {'supergpqa': '31000', 'bbeh': '31256', 'mmlupro': '31512'})
