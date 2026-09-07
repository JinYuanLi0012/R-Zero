import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from evaluation import evaluate_models as batch


class EvaluateModelsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='rzero-batch-test-'))
        self.paths = []
        for name in ('group_A_solver_v1', 'group_A_solver_v2', 'other group_solver_v1', 'another_checkpoint'):
            run = self.root / name
            config = run / 'global_step_15/actor/huggingface/config.json'
            config.parent.mkdir(parents=True)
            config.write_text('{}')
            self.paths.append(str(config.parent) if name == 'another_checkpoint' else str(run))
        self.output = self.root / 'batch'
        self.env = patch.dict(os.environ, {'STORAGE_PATH': str(self.root)}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def emit(self, command, cwd, env):
        self.assertEqual(env['RECHECK_BACKEND'], 'local')
        self.assertEqual(env['RECHECK_LOCAL_MODEL'], 'Qwen/Qwen3-32B')
        self.assertEqual(env['EVAL_TASKS'], ','.join(batch.DATASETS))
        path = Path(env['FINAL_RESULTS_FILE'])
        path.write_text(''.join(json.dumps({'model': command[-1], 'dataset': d,
                       'score': 70 + i, 'recheck': batch.JUDGE}) + '\n'
                       for i, d in enumerate(batch.DATASETS)))
        return 0

    def test_arbitrary_paths_and_summary_only(self):
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output)] + self.paths), \
             patch.object(batch.subprocess, 'call', side_effect=self.emit) as call:
            batch.main()
            self.assertEqual(call.call_count, 4)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(len(manifest['models']), 4)
        self.assertTrue(all(item['status'] == 'complete' for item in manifest['models']))
        self.assertEqual(len((self.output / 'summary.csv').read_text().splitlines()), 5)
        with patch.object(sys, 'argv', ['runner', '--summary-only', str(self.output)]), \
             patch.object(batch.subprocess, 'call') as call:
            batch.main()
            call.assert_not_called()

    def test_stop_on_failure_and_keep_missing_cells_empty(self):
        def fail(command, cwd, env):
            self.emit(command, cwd, env)
            return 1
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output)] + self.paths), \
             patch.object(batch.subprocess, 'call', side_effect=fail) as call:
            with self.assertRaises(SystemExit):
                batch.main()
            self.assertEqual(call.call_count, 1)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        rows = batch.summarize(self.output, manifest)
        self.assertEqual(rows[0][2], 'failed')
        self.assertEqual(rows[0][10], '')
        self.assertEqual(rows[1][2], 'pending')
        self.assertEqual(rows[1][3:11], [''] * 8)

    def test_duplicate_or_different_judge_not_accepted(self):
        item = batch.plan(self.paths)[0]
        item.update(status='complete', results_file='results.jsonl')
        self.output.mkdir()
        record = dict(model=item['model'], dataset='math', score=77.2, recheck=batch.JUDGE)
        result = self.output / item['results_file']
        result.write_text(json.dumps(record) + '\n' + json.dumps(record) + '\n')
        manifest = dict(judge=batch.JUDGE, models=[item])
        self.assertEqual(batch.summarize(self.output, manifest)[0][2], 'invalid_results')
        record['recheck'] = {'backend': 'api'}
        result.write_text(json.dumps(record) + '\n')
        self.assertEqual(batch.summarize(self.output, manifest)[0][2], 'invalid_results')

    def test_dry_run_has_no_outputs_or_processes(self):
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output), '--dry-run'] + self.paths), \
             patch.object(batch.subprocess, 'call') as call:
            batch.main()
            call.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_paths_expand_correctly_and_same_basename_keeps_unique_ids(self):
        models = batch.plan(self.paths)
        self.assertEqual(models[0]['model'], str(Path(self.paths[0]) / 'global_step_15/actor/huggingface'))
        self.assertEqual(models[-1]['model'], self.paths[-1])
        other = self.root / 'elsewhere' / Path(self.paths[0]).name
        config = other / 'global_step_15/actor/huggingface/config.json'
        config.parent.mkdir(parents=True)
        config.write_text('{}')
        two = batch.plan([self.paths[0], str(other)])
        self.assertEqual(two[0]['name'], two[1]['name'])
        self.assertNotEqual(two[0]['results_file'], two[1]['results_file'])

    def test_duplicate_and_missing_paths_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            batch.plan([self.paths[0], self.paths[0] + '/global_step_15/actor/huggingface'])
        with self.assertRaisesRegex(ValueError, 'Missing'):
            batch.plan([str(self.root / 'missing')])

    def test_output_storage_independent_of_model_paths(self):
        storage = self.root / 'different_storage'
        def emit(command, cwd, env):
            self.assertEqual(env['STORAGE_PATH'], str(storage))
            return self.emit(command, cwd, env)
        with patch.object(sys, 'argv', ['runner', '--storage-path', str(storage), '--batch-dir', str(self.output)] + self.paths[:1]), \
             patch.object(batch.subprocess, 'call', side_effect=emit):
            batch.main()
        self.assertTrue((self.output / 'summary.csv').is_file())


if __name__ == '__main__':
    unittest.main()
