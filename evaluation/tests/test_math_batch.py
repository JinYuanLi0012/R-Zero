import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from evaluation import run_math_batch as batch


class MathBatchTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='rzero-batch-test-'))
        for item in batch.plan(self.root):
            config = Path(item['model']) / 'config.json'
            config.parent.mkdir(parents=True)
            config.write_text('{}')
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

    def test_all_15_and_summary_only(self):
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output)]), \
             patch.object(batch.subprocess, 'call', side_effect=self.emit) as call:
            batch.main()
            self.assertEqual(call.call_count, 15)
        manifest = json.loads((self.output / 'manifest.json').read_text())
        self.assertEqual(len(manifest['models']), 15)
        self.assertTrue(all(item['status'] == 'complete' for item in manifest['models']))
        self.assertEqual(len((self.output / 'summary.csv').read_text().splitlines()), 16)
        with patch.object(sys, 'argv', ['runner', '--summary-only', str(self.output)]), \
             patch.object(batch.subprocess, 'call') as call:
            batch.main()
            call.assert_not_called()

    def test_stop_on_failure_and_keep_missing_cells_empty(self):
        def fail(command, cwd, env):
            self.emit(command, cwd, env)
            return 1
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output)]), \
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
        item = batch.plan(self.root)[0]
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
        with patch.object(sys, 'argv', ['runner', '--batch-dir', str(self.output), '--dry-run']), \
             patch.object(batch.subprocess, 'call') as call:
            batch.main()
            call.assert_not_called()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
