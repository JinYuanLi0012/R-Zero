import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch, Mock

from methods.validity_rzero.three_question_pilot import train_solver as target


class TrainSolverTest(unittest.TestCase):
    def test_prepare_launch_and_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / 'data'
            data.mkdir()
            rows = [dict(sample_id=str(i), question='q', answer='majority',
                         questioner_answer='wrong', score=.5) for i in range(5633)]
            (data / 'round_4.json').write_text(json.dumps(rows))
            (data / 'round_4_phase_b.jsonl').write_text('\n'.join(map(json.dumps, rows)))
            terra = [dict(id=str(i), question='t', split='train',
                          terra_validity='INVALID', validity_rl_target='INVALID') for i in range(1000)]
            pushed = Mock()
            class DatasetDict(dict):
                def push_to_hub(self, *args, **kwargs):
                    pushed(self, *args, **kwargs)
            fake = types.SimpleNamespace(Dataset=types.SimpleNamespace(from_list=lambda x: x),
                                         DatasetDict=DatasetDict, load_dataset=Mock(return_value=terra))
            argv = ['train', '--data-dir', str(data), '--storage-path', str(root)]
            with patch.dict('sys.modules', {'datasets': fake, 'huggingface_hub': types.SimpleNamespace(login=Mock())}), \
                 patch.object(target, 'resolve_model', return_value=('/S3/global_step_15/actor/huggingface', {})), \
                 patch.object(target.subprocess, 'check_output', return_value='testcommit'), \
                 patch.object(target.subprocess, 'run') as run, \
                 patch.dict(target.os.environ, {'SOLVER_MAX_STEPS': '99', 'SOLVER_LOAD_CHECKPOINT': '/wrong',
                                               'HUGGINGFACENAME': 'test'}), \
                 patch('builtins.print'):
                with patch('sys.argv', argv + ['--prepare-only']):
                    target.main()
                run.assert_not_called()
                mixed = pushed.call_args.args[0]['train']
                self.assertEqual(len(mixed), 6258)
                self.assertEqual(sum(r['source'] == 'terra' for r in mixed), 625)
                self.assertTrue(all(r['answer'] == 'majority' for r in mixed if r['source'] == 'rzero'))
                with patch('sys.argv', argv):
                    target.main()
                self.assertEqual(pushed.call_count, 1)
                env = run.call_args.kwargs['env']
                self.assertEqual(env['SOLVER_MAX_STEPS'], '15')
                self.assertEqual(env['SOLVER_DATASET_READY'], '1')
                self.assertNotIn('SOLVER_LOAD_CHECKPOINT', env)
                self.assertIn('/S3/global_step_15/actor/huggingface', run.call_args.args[0])
                (root / 'models' / target.NAME).mkdir(parents=True)
                with patch('sys.argv', argv), self.assertRaises(FileExistsError):
                    target.main()
            rows[0]['answer'] = 'changed'
            (data / 'round_4.json').write_text(json.dumps(rows))
            with self.assertRaises(ValueError):
                target.read_retained(data)


if __name__ == '__main__':
    unittest.main()
