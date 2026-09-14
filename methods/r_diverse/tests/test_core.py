import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from methods.r_diverse.core import (batch_penalties, memory_penalties, parse_question,
                                    replay_rows, retained, write_json, read_json)
from methods.r_diverse.run import clean_environment, train


class CoreTests(unittest.TestCase):
    def test_map_matches_explicit_cosines(self):
        rng = np.random.default_rng(2)
        x, m = rng.normal(size=(7, 8)), rng.normal(size=(5000, 8))
        similarity = (x / np.linalg.norm(x, axis=1, keepdims=True)) @ (
            m / np.linalg.norm(m, axis=1, keepdims=True)).T
        penalty, maximum, mean = memory_penalties(x, m)
        np.testing.assert_allclose(maximum, similarity.max(axis=1), atol=2e-6)
        np.testing.assert_allclose(mean, similarity.mean(axis=1), atol=2e-6)
        expected = .5 * np.maximum(similarity.max(axis=1) - .5, 0)
        expected += .5 * np.maximum(similarity.mean(axis=1) - .25, 0)
        np.testing.assert_allclose(penalty, expected, atol=2e-6)

    def test_mean_is_not_renormalized(self):
        penalty, maximum, mean = memory_penalties([[1., 0]], [[1., 0], [0., 1]])
        self.assertAlmostEqual(mean[0], .5)
        self.assertAlmostEqual(penalty[0], .375)

    def test_empty_history(self):
        for result in memory_penalties([[1., 0]], np.empty((0, 2))):
            np.testing.assert_array_equal(result, [0.])

    def test_cluster_multiplicity(self):
        penalty = batch_penalties([[1., 0], [1., 0], [0., 1]])
        np.testing.assert_allclose(penalty, [2 / 3, 2 / 3, 1 / 3])

    def test_all_same_and_singleton(self):
        np.testing.assert_allclose(batch_penalties([[1., 0]] * 4), np.ones(4))
        np.testing.assert_allclose(batch_penalties([[1., 0]]), [1.])

    def test_duplicate_history_weights_mean(self):
        _, _, mean = memory_penalties([[1., 0]], [[1., 0], [1., 0], [0., 1]])
        self.assertAlmostEqual(mean[0], 2 / 3, places=6)

    def test_replay_fraction_and_no_mutation(self):
        current = [{'question': str(i), 'source_round': 2} for i in range(7)]
        history = [{'question': f'old{i}', 'source_round': 1} for i in range(8)]
        mixed = replay_rows(current, history, seed=3)
        self.assertEqual(len(mixed), 10)
        self.assertEqual(sum(r['replay'] for r in mixed), 3)
        self.assertEqual(mixed, replay_rows(current, history, seed=3))
        self.assertNotIn('replay', current[0])
        self.assertNotIn('replay', history[0])

    def test_small_and_empty_history(self):
        current = [{'question': str(i)} for i in range(70)]
        self.assertEqual(len(replay_rows(current, [])), 70)
        mixed = replay_rows(current, [{'question': 'old'}])
        self.assertEqual(len(mixed), 100)
        self.assertEqual(sum(r['question'] == 'old' for r in mixed), 30)

    def test_parser_and_filter(self):
        text = r'<question>old</question><question> new </question>\boxed{\frac{1}{2}}'
        row = parse_question(text)
        self.assertEqual(row['question'], 'new')
        self.assertEqual(row['answer'], r'\frac{1}{2}')
        self.assertFalse(parse_question('<question>x</question>')['question'])
        for score in [.3, .8]:
            self.assertTrue(retained(dict(row, score=score)))
        self.assertFalse(retained(dict(row, score=.9)))
        self.assertFalse(retained(dict(row, score=.5, question='证明 x')))

    def test_json_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'x.json'
            write_json(path, {'round': 1})
            write_json(path, {'round': 2})
            self.assertEqual(read_json(path), {'round': 2})

    def test_environment_isolation(self):
        with patch.dict(os.environ, {'VALIDITY_RZERO_ENABLED': '1', 'TERRA_REPLAY_RATIO': '.1',
                                     'RZERO_DOMAIN_ENABLED': '1', 'STORAGE_PATH': '/keep'}):
            clean_environment()
            self.assertEqual(os.environ['VALIDITY_RZERO_ENABLED'], '0')
            self.assertNotIn('TERRA_REPLAY_RATIO', os.environ)
            self.assertNotIn('RZERO_DOMAIN_ENABLED', os.environ)
            self.assertEqual(os.environ['STORAGE_PATH'], '/keep')

    def test_training_four_gpu_overrides(self):
        calls = []
        def fake_command(args, log, gpus=None):
            calls.append((args, gpus))
            if '--local_dir' in args:
                hf = Path(args[-1]) / 'huggingface'
                hf.mkdir(parents=True)
                (hf / 'config.json').write_text('{}')
        cfg = {'questioner_gpus': ['0','1'], 'all_gpus': ['0','1','2','3'],
               'rollout_batch': 512, 'seed': 1, 'response_tokens': 4096,
               'run_name': 'baseline', 'logger': '["console"]', 'questioner_global_batch': 4}
        with tempfile.TemporaryDirectory() as temp, patch('methods.r_diverse.run.command', fake_command):
            for role in ['questioner', 'solver']:
                train(role, 'base', 'data.parquet', cfg, 'config.json', Path(temp), 'memory.npy', 'solver')
        q, s = calls[0], calls[2]
        self.assertEqual(q[1], ['0', '1'])
        self.assertIn('worker.actor.global_batch_size=4', q[0])
        self.assertIn('worker.rollout.n=4', q[0])
        self.assertEqual(s[1], ['0', '1', '2', '3'])
        self.assertIn('worker.rollout.n=5', s[0])
        self.assertIn('trainer.max_steps=15', s[0])

    def test_sampling_does_not_seed_each_identical_request(self):
        # A fixed SamplingParams seed for every fixed-prompt request would clone Q outputs.
        source = Path(__file__).parents[1] / 'gpu_worker.py'
        tree = ast.parse(source.read_text())
        params = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute) and node.func.attr == 'SamplingParams']
        self.assertTrue(params)
        self.assertTrue(all('seed' not in [kw.arg for kw in call.keywords] for call in params))


if __name__ == '__main__':
    unittest.main()
