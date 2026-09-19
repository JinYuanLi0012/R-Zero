"""CPU coverage of real tokenizer serialization and Q/S inference boundaries."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.processors import TemplateProcessing
from transformers import AutoTokenizer, LlamaConfig, PreTrainedTokenizerFast

from methods.r_diverse.backbone import (
    generation_inputs, inference_tokenizer_path, prepare_backbone_tokenizer,
)
from methods.r_diverse.gpu_worker import generate, render
from methods.r_diverse.prompts import QUESTIONER_MESSAGES, SOLVER_SYSTEM
from methods.r_diverse.run import train


class BackboneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.source = cls.root / 'base'
        # Tiny behavior fixture, with Octo's actual special-token IDs and BOS
        # postprocessor. No pretrained model, weights, GPU or network required.
        vocab = {f'token_{i}': i for i in range(128000)}
        vocab.update({'<|begin_of_text|>': 128000, '<|end_of_text|>': 128001})
        backend = Tokenizer(WordLevel(vocab, unk_token='token_0'))
        backend.post_processor = TemplateProcessing(
            single='<|begin_of_text|> $A',
            special_tokens=[('<|begin_of_text|>', 128000)])
        tokenizer = PreTrainedTokenizerFast(
            tokenizer_object=backend, unk_token='token_0',
            bos_token='<|begin_of_text|>', eos_token='<|end_of_text|>')
        tokenizer.save_pretrained(cls.source)
        LlamaConfig(bos_token_id=128000, eos_token_id=128001).save_pretrained(cls.source)
        cls.prepared = prepare_backbone_tokenizer(cls.source, cls.root / 'prepared', 'octothinker')
        cls.tokenizer = AutoTokenizer.from_pretrained(cls.prepared)
        cls.config = {'backbone_prompt': 'octothinker', 'backbone_tokenizer': cls.prepared}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_round_trip_and_training_inference_eval_ids_match(self):
        from evaluation.prompt_inputs import generation_inputs as eval_inputs

        messages_by_role = [QUESTIONER_MESSAGES,
                            [{'role': 'system', 'content': SOLVER_SYSTEM},
                             {'role': 'user', 'content': 'What is 2 + 2?'}]]
        for mode, messages in zip(['generate', 'solve'], messages_by_role):
            with self.subTest(mode=mode):
                prompt = render(self.tokenizer, messages)
                self.assertEqual(prompt, '<|begin_of_text|>' + ''.join(
                    m['role'] + ': ' + m['content'] + '\n' for m in messages) + 'assistant:\n')
                # This is the dataset's apply_chat_template -> raw_prompt_ids path.
                training_ids = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True)
                inference_ids = generation_inputs([prompt], self.tokenizer, self.config, mode)
                self.assertEqual(inference_ids, [{'prompt_token_ids': training_ids}])
                self.assertEqual(training_ids.count(128000), 1)
                self.assertEqual(training_ids[0], 128000)
                # Demonstrate the duplicate BOS that passing strings would allow.
                self.assertEqual(self.tokenizer.encode(prompt)[:2], [128000, 128000])
                # FSDP saves this tokenizer with each checkpoint. Reload repeatedly
                # to verify that later rounds/evaluation retain the same wrapper.
                tokenizer = self.tokenizer
                for number in range(1, 6):
                    saved = self.root / f'{mode}_checkpoint_{number}'
                    tokenizer.save_pretrained(saved)
                    tokenizer = AutoTokenizer.from_pretrained(saved)
                    self.assertEqual(tokenizer.pad_token_id, 128001)
                    self.assertEqual(tokenizer.eos_token_id, 128001)
                    self.assertEqual(tokenizer.apply_chat_template(messages, add_generation_prompt=True), training_ids)
                    self.assertEqual(eval_inputs([render(tokenizer, messages)], tokenizer), inference_ids)
        self.assertIsNone(AutoTokenizer.from_pretrained(self.source).chat_template)

    def test_worker_uses_current_weights_but_shared_tokenizer_for_both_roles(self):
        for mode in ['generate', 'solve']:
            seen = {}

            class LLM:
                def __init__(self, **kwargs):
                    seen['engine'] = kwargs

                def generate(self, prompts, params, **kwargs):
                    seen['inputs'] = prompts
                    return [SimpleNamespace(outputs=[SimpleNamespace(
                        text='<question>What is 2 + 2?</question>\\boxed{4}')])]

            job = dict(mode=mode, model='current-round-weights', seed=1, phase='label',
                       rows=[dict(question='What is 2 + 2?')],
                       config=dict(self.config, inference_memory=.8, inference_context=8192,
                                   response_tokens=64, inference_batch=1))
            with patch.dict('sys.modules', vllm=SimpleNamespace(LLM=LLM, SamplingParams=lambda **kw: kw)), \
                    patch('methods.r_diverse.gpu_worker.majority', return_value={'answer': '4', 'score': 1.}):
                self.assertEqual(len(generate(job)), 1)
            self.assertEqual(seen['engine']['model'], 'current-round-weights')
            self.assertEqual(seen['engine']['tokenizer'], self.prepared)
            self.assertEqual(seen['inputs'][0]['prompt_token_ids'][0], 128000)

    def test_coder_and_native_paths_are_unchanged(self):
        prompts = ['Output:\n<CODE>\n']
        self.assertIs(generation_inputs(prompts, self.tokenizer, self.config, 'code'), prompts)
        self.assertEqual(inference_tokenizer_path('coder', self.config, 'code'), 'coder')
        self.assertEqual(inference_tokenizer_path('encoder', self.config, 'embed'), 'encoder')
        self.assertIs(generation_inputs(prompts, self.tokenizer, {}, 'generate'), prompts)
        self.assertEqual(inference_tokenizer_path('qwen', {}, 'solve'), 'qwen')
        self.assertEqual(prepare_backbone_tokenizer('qwen', self.root / 'unused', 'native'), 'qwen')
        self.assertFalse((self.root / 'unused').exists())

    def test_training_passes_tokenizer_to_checkpoint_workers_for_both_roles(self):
        cfg = dict(self.config, questioner_gpus=['0', '1'], all_gpus=['0', '1', '2', '3'],
                   rollout_batch=512, seed=1, response_tokens=4096, run_name='test',
                   logger='["console"]', questioner_global_batch=4)
        for role, steps in [('questioner', 5), ('solver', 15)]:
            directory = self.root / f'train_{role}'
            directory.mkdir()
            saved = directory / role / 'attempt_1' / f'global_step_{steps}' / 'actor' / 'huggingface'

            def command(args, *unused):
                if args[1] == 'scripts/model_merger.py':
                    saved.mkdir(parents=True)
                    (saved / 'config.json').write_text('{}')

            with patch('methods.r_diverse.run.command', side_effect=command) as run_command:
                self.assertEqual(train(role, 'current-weights', 'data.parquet', cfg, 'config.json',
                                       directory, 'memory.npy', 'solver-weights'), str(saved))
            argv = run_command.call_args_list[0].args[0]
            self.assertIn('worker.actor.model.model_path=current-weights', argv)
            self.assertIn(f'worker.actor.model.tokenizer_path={self.prepared}', argv)


if __name__ == '__main__':
    unittest.main()
