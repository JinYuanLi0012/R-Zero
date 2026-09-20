import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('paired_run', Path(__file__).resolve().parents[1] / 'run.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.original = [dict(id='a', problem='same', answer='2', score=0.5, label_job_id='a'),
                         dict(id='b', problem='original', answer='3', score=0.4, label_job_id='b')]
        self.repaired = copy.deepcopy(self.original)
        self.repaired[1].update(problem='repaired', answer='4', label_job_id='c')

    def test_pairs(self):
        self.assertEqual(m.validate_pairs(self.original, self.repaired), dict(pairs=2, shared=1, changed=1))

    def test_reject_reordering_and_bad_shared_labels(self):
        with self.assertRaises(ValueError):
            m.validate_pairs(self.original, self.repaired[::-1])
        self.repaired[0]['answer'] = '9'
        with self.assertRaises(ValueError):
            m.validate_pairs(self.original, self.repaired)

    def test_reject_sentinel(self):
        self.repaired[1]['answer'] = 'None'
        with self.assertRaises(ValueError):
            m.validate_pairs(self.original, self.repaired)

    def test_environment_isolation(self):
        with patch.dict(os.environ, {'VALIDITY_RZERO_ENABLED': '1', 'SOLVER_DYNAMIC_VOTE': '1',
                                     'RAY_ADDRESS': 'remote', 'HF_HUB_CACHE': '/cache'}):
            env = m.clean_environment('4,5,6,7', Path('/tmp/run'), 1)
            self.assertNotIn('VALIDITY_RZERO_ENABLED', env)
            self.assertNotIn('SOLVER_DYNAMIC_VOTE', env)
            self.assertEqual(env['RAY_ADDRESS'], 'local')
            self.assertEqual(env['HF_HUB_CACHE'], '/cache')
            self.assertEqual(env['CUDA_VISIBLE_DEVICES'], '4,5,6,7')
            self.assertEqual(os.environ['RAY_ADDRESS'], 'remote')

    def test_jsonl_unicode_line_separator(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.jsonl'
            path.write_text('{"text":"a\u2028b"}\n')
            self.assertEqual(len(m.read_rows(path)), 1)

    def test_resume_uses_committed_tracker(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            root = directory / 'checkpoints'
            (root / 'global_step_5').mkdir(parents=True)
            (root / 'global_step_10').mkdir()  # interrupted, incomplete save
            (root / 'global_step_5/dataloader.pt').touch()
            with self.assertRaises(ValueError):
                m.resume_checkpoint(directory)
            (root / 'latest_global_step.txt').write_text('5')
            self.assertEqual(m.resume_checkpoint(directory), root / 'global_step_5')


if __name__ == '__main__':
    unittest.main()
