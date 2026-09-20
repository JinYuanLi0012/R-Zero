"""CPU regression checks; no model loading, network or GPU calls."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from methods.ocnr import run
from methods.validity_rzero import octothinker


class BackboneTests(unittest.TestCase):
    def setUp(self):
        self.native = json.loads((run.ROOT / 'methods/ocnr/config.json').read_text())
        self.octo = json.loads((run.ROOT / 'methods/ocnr/config_octothinker.json').read_text())
        self.inherited = {'VALIDITY_RZERO_ENABLED': '1',
                          'VALIDITY_RZERO_MODEL_FAMILY': 'octothinker',
                          'VALIDITY_RZERO_FROZEN_JUDGE_MODEL': '/unwanted',
                          'TERRA_REPLAY_RATIO': '0.1', 'OCNR_STALE': '1',
                          'STORAGE_PATH': '/storage', 'PATH': '/bin'}

    def test_only_backbone_and_experiment_change(self):
        difference = {k for k in self.native.keys() | self.octo.keys()
                      if self.native.get(k) != self.octo.get(k)}
        self.assertEqual(difference, {'base_model', 'run_name', 'backbone_prompt'})

    def test_native_resume_config_and_environment_stay_compatible(self):
        before = self.native.copy()
        env = run.build_environment(self.native, self.inherited)
        self.assertEqual(self.native, before)
        self.assertEqual(env['VALIDITY_RZERO_ENABLED'], '0')
        self.assertNotIn('VALIDITY_RZERO_MODEL_FAMILY', env)
        self.assertEqual(env['STORAGE_PATH'], '/storage')
        self.assertFalse(any(k.startswith(('TERRA_REPLAY_', 'OCNR_')) for k in env))

    def test_octo_restores_only_template_switch(self):
        env = run.build_environment(self.octo, self.inherited)
        self.assertEqual({k: v for k, v in env.items() if k.startswith('VALIDITY_RZERO_')},
                         {'VALIDITY_RZERO_ENABLED': '0', 'VALIDITY_RZERO_MODEL_FAMILY': 'octothinker'})
        class Tokenizer:
            bos_token = '<|begin_of_text|>'
            eos_token = '<|end_of_text|>'
            pad_token_id = None
            def encode(self, text, add_special_tokens):
                self.add_special_tokens = add_special_tokens
                return [128000, 42]
        tokenizer = Tokenizer()
        with patch.dict(os.environ, env, clear=True):
            octothinker.configure_tokenizer(tokenizer)
            self.assertIn("'assistant:\\n'", tokenizer.chat_template)
            self.assertEqual(tokenizer.pad_token, tokenizer.eos_token)
            self.assertEqual(octothinker.generation_inputs(['rendered'], tokenizer),
                             [{'prompt_token_ids': [128000, 42]}])
            self.assertFalse(tokenizer.add_special_tokens)

    def test_q_and_s_subprocesses_receive_octo_environment(self):
        env = run.build_environment(self.octo, self.inherited)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for role in ['questioner', 'solver']:
                with patch.object(run, 'execute') as execute, patch.object(run, 'merged_model_ready', return_value=True):
                    run.train(role, self.octo['base_model'], root / role, root / 'data.parquet',
                              self.octo, env, root / 'log', False, services=2)
                    command, child_env, _ = execute.call_args_list[0].args
                    self.assertIn('worker.actor.model.model_path=' + self.octo['base_model'], command)
                    self.assertEqual(child_env['VALIDITY_RZERO_MODEL_FAMILY'], 'octothinker')
                    self.assertEqual(child_env['VALIDITY_RZERO_ENABLED'], '0')
                    self.assertEqual(child_env['CUDA_VISIBLE_DEVICES'], '0,1' if role == 'questioner' else '0,1,2,3')

    def test_unknown_prompt_fails(self):
        with self.assertRaises(ValueError):
            run.build_environment({**self.octo, 'backbone_prompt': 'typo'}, self.inherited)


if __name__ == '__main__':
    unittest.main()
