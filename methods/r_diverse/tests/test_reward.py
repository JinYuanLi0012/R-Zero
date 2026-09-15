from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from methods.r_diverse.core import read_json, write_json
from methods.r_diverse.reward import compute_score


class RewardTests(unittest.TestCase):
    def test_malformed_below_worst_parseable_with_map_and_order_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'config.json'
            memory = root / 'memory.npy'
            write_json(config, {'feedback_gpus': ['2', '3'], 'seed': 1})
            np.save(memory, np.array([[1., 0.]], dtype=np.float32))
            # Both valid questions share a cluster and exactly match history:
            # local=1, MAP=0.625. A frontier of 0 attains the -1.625 lower bound.
            predicts = ['```', '<question>q1</question>\\boxed{1}',
                        '<question>q2</question>\\boxed{2}', '<question>missing answer</question>']
            evaluated = [{'question': 'q1', 'score': 0.0}, {'question': 'q2', 'score': 0.5}]
            with patch('methods.r_diverse.reward.run_workers', return_value=evaluated) as solve, \
                 patch('methods.r_diverse.reward.sam', return_value=(
                     np.array([[1., 0.], [1., 0.]], dtype=np.float32),
                     [{'key': 'q1'}, {'key': 'q2'}])) as sam:
                scores = compute_score(predicts, [''] * 4, config, 'solver', memory, root)
            self.assertEqual([s['overall'] for s in scores], [-2., -1.625, -1.125, -2.])
            self.assertEqual([s['format'] for s in scores], [0., 1., 1., 0.])
            self.assertEqual([r['question'] for r in solve.call_args.args[1]], ['q1', 'q2'])
            self.assertEqual(sam.call_args.args[0], ['q1', 'q2'])
            for score in scores[1:3]:
                self.assertEqual(score['batch_penalty'], 1.)
                self.assertEqual(score['map_penalty'], .625)
                self.assertEqual(score['overall'], score['frontier'] - score['batch_penalty'] - score['map_penalty'])
            artifacts = next(root.glob('reward_*'))
            self.assertEqual(read_json(artifacts / 'scores.json'), scores)
            self.assertEqual([r['original_index'] for r in read_json(artifacts / 'questions.json')], [1, 2])

    def test_all_malformed_needs_no_inference_or_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'config.json'
            write_json(config, {})
            with patch('methods.r_diverse.reward.run_workers') as solve, \
                 patch('methods.r_diverse.reward.sam') as sam:
                scores = compute_score(['', 'question>', '\\boxed{1}'], [''] * 3,
                                       config, 'solver', root / 'absent.npy', root)
            solve.assert_not_called()
            sam.assert_not_called()
            self.assertEqual([s['overall'] for s in scores], [-2.] * 3)


if __name__ == '__main__':
    unittest.main()
