"""CPU contracts for prompt compatibility, CLI propagation, and result isolation."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from evaluation import evaluate_models as batch, judge_prompts as prompts
from evaluation import recheck_resume, run_local_recheck
from evaluation.local_judge import LocalJudge, judge_metadata

ROOT = Path(__file__).resolve().parents[2]
# Exact upstream 5699329d018d79535b7910abdedf5a6eebf355fd messages,
# rendered with its process_example(reference, solver) call convention.
ORIGINAL = [
    {'role': 'system', 'content': 'You are a math answer checker.'},
    {'role': 'user', 'content': 'Hi, there is a answer: REFERENCE\n\n, and the ground truth answer is: SOLVER\n\n, please check whether the answer is correct or not, and return the **only** Yes or No.'},
]
CORRECTED = [
    ORIGINAL[0],
    {'role': 'user', 'content': 'Hi, there is a model response: SOLVER\n\n, and the ground truth answer is: REFERENCE\n\n, please check whether the model response is correct or not, and return the **only** Yes or No.'},
]


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='rzero-prompt-test-'))
        self.env = patch.dict(os.environ, {'RECHECK_BACKEND': 'local', 'STORAGE_PATH': str(self.root)}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def response(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {'choices': [{'message': {'content': 'Yes'}, 'finish_reason': 'stop'}]}
        return response

    def test_exact_upstream_and_unchanged_corrected_bytes(self):
        self.assertEqual(prompts.messages('REFERENCE', 'SOLVER'), CORRECTED)
        self.assertEqual(prompts.messages('REFERENCE', 'SOLVER', 'rzero-original'), ORIGINAL)
        self.assertEqual(prompts.messages('REFERENCE', 'SOLVER', 'rzero-original', resume_api=True), ORIGINAL)
        expected = [CORRECTED[0], dict(CORRECTED[1], content=CORRECTED[1]['content'].replace('\n\n, please', '\n\nplease'))]
        self.assertEqual(prompts.messages('REFERENCE', 'SOLVER', resume_api=True), expected)
        self.assertEqual(prompts.prompt_metadata('rzero-original')['prompt_source_commit'],
                         '5699329d018d79535b7910abdedf5a6eebf355fd')

    def test_actual_local_and_api_payloads(self):
        for mode, expected in [('corrected', CORRECTED), ('rzero-original', ORIGINAL)]:
            with self.subTest(mode=mode), patch.dict(os.environ, {'RECHECK_JUDGE_PROMPT_MODE': mode}):
                with patch('evaluation.local_judge.requests.Session') as factory:
                    post = factory.return_value.__enter__.return_value.post
                    post.return_value = self.response()
                    LocalJudge()('REFERENCE', 'SOLVER')
                    self.assertEqual(post.call_args.kwargs['json']['messages'], expected)
                with patch.dict(os.environ, {'RECHECK_BACKEND': 'api', 'OPENAI_API_KEY': 'test-only'}):
                    module = runpy.run_path(str(ROOT / 'evaluation/results_recheck.py'))
                    with patch('requests.post', return_value=self.response()) as post:
                        module['process_example']('REFERENCE', 'SOLVER')
                        self.assertEqual(post.call_args.kwargs['json']['messages'], expected)
                        recheck_resume.judge_model_response('http://test/v1/chat/completions', 'test-only', 'REFERENCE', 'SOLVER')
                        resume_expected = expected if mode == 'rzero-original' else [expected[0], dict(expected[1], content=expected[1]['content'].replace('\n\n, please', '\n\nplease'))]
                        self.assertEqual(post.call_args.kwargs['json']['messages'], resume_expected)

    def test_output_and_resume_isolate_modes_and_accept_old_corrected(self):
        output = self.root / 'scores.jsonl'
        old = judge_metadata()
        old.pop('prompt_mode')
        output.write_text(json.dumps({'model': 'solver', 'dataset': 'math', 'score': 50, 'recheck': old}) + '\n')
        prompts.ensure_output_mode(output, 'corrected')
        self.assertEqual(recheck_resume.load_completed(output, judge_metadata()), {('solver', 'math')})
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            prompts.ensure_output_mode(output, 'rzero-original')
        with patch.dict(os.environ, {'RECHECK_JUDGE_PROMPT_MODE': 'rzero-original'}):
            self.assertEqual(recheck_resume.load_completed(output, judge_metadata()), set())
            output.write_text(json.dumps({'model': 'solver', 'dataset': 'math', 'score': 50, 'recheck': judge_metadata()}) + '\n')
            self.assertEqual(recheck_resume.load_completed(output, judge_metadata()), {('solver', 'math')})
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            prompts.ensure_output_mode(output, 'corrected')
        self.assertEqual(recheck_resume.load_completed(output, judge_metadata()), set())

    def test_results_cli_and_resume_refuse_cross_mode_before_requests(self):
        output = self.root / 'scores.jsonl'
        output.write_text(json.dumps({'model': 'solver', 'dataset': 'math', 'score': 50}) + '\n')
        before = output.read_bytes()
        os.environ['FINAL_RESULTS_FILE'] = str(output)
        with patch('requests.Session') as session:
            with patch.object(sys, 'argv', ['results', '--model_name', 'solver', '--judge-prompt-mode', 'rzero-original']):
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    runpy.run_path(str(ROOT / 'evaluation/results_recheck.py'), run_name='__main__')
            with patch.object(sys, 'argv', ['resume', '--models_file', 'unused', '--output_file', str(output), '--judge-prompt-mode', 'rzero-original']):
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    recheck_resume.main()
            session.assert_not_called()
        self.assertEqual(output.read_bytes(), before)

    def test_original_results_cli_writes_mode_and_preserves_raw_results(self):
        raw = self.root / 'evaluation/solver/results_math.json'
        raw.parent.mkdir(parents=True)
        raw.write_text('[{"answer":"REFERENCE","response":"SOLVER","score":0},{}]')
        before = raw.read_bytes()
        output = self.root / 'original.jsonl'
        os.environ['FINAL_RESULTS_FILE'] = str(output)
        argv = ['results', '--model_name', 'solver', '--datasets', 'math', '--judge-prompt-mode', 'rzero-original']
        with patch.object(sys, 'argv', argv), patch('evaluation.local_judge.requests.Session') as factory:
            post = factory.return_value.__enter__.return_value.post
            post.return_value = self.response()
            runpy.run_path(str(ROOT / 'evaluation/results_recheck.py'), run_name='__main__')
            self.assertEqual(post.call_args.kwargs['json']['messages'], ORIGINAL)
        record = json.loads(output.read_text())
        self.assertEqual(record['score'], 100)
        self.assertEqual(record['recheck']['prompt_mode'], 'rzero-original')
        self.assertEqual(record['recheck']['prompt_version'], 'rzero-original-5699329d-v1')
        self.assertEqual(raw.read_bytes(), before)

    def test_runner_passes_mode_to_client(self):
        raw = self.root / 'evaluation/solver/results_math.json'
        raw.parent.mkdir(parents=True)
        raw.write_text('[{"answer":"REFERENCE","response":"SOLVER","score":0},{}]')
        os.environ['EVAL_LOG_DIR'] = str(self.root / 'logs')
        server, client = MagicMock(), MagicMock()
        client.wait.return_value = 0
        argv = ['runner', '--model_name', 'solver', '--datasets', 'math', '--output_file', str(self.root / 'out.jsonl'), '--judge-prompt-mode', 'rzero-original']
        with patch.object(sys, 'argv', argv), patch.object(run_local_recheck.subprocess, 'Popen', side_effect=[server, client]) as popen, patch.object(run_local_recheck, 'wait_ready'), patch.object(run_local_recheck, 'stop_owned_process'):
            run_local_recheck.main()
        child_env = popen.call_args_list[1].kwargs['env']
        self.assertEqual(child_env['RECHECK_JUDGE_PROMPT_MODE'], 'rzero-original')
        with patch.dict(os.environ, child_env, clear=True):
            self.assertEqual(LocalJudge().metadata['prompt_mode'], 'rzero-original')

    def test_batch_modes_summary_and_checkpoint_copy(self):
        config = self.root / 'solver/global_step_15/actor/huggingface/config.json'
        config.parent.mkdir(parents=True)
        config.write_text('{}')
        # A stale shell env must not silently change the batch default.
        os.environ['RECHECK_JUDGE_PROMPT_MODE'] = 'rzero-original'
        for mode in prompts.MODES:
            def emit(command, cwd, env):
                self.assertEqual(env['RECHECK_JUDGE_PROMPT_MODE'], mode)
                with patch.dict(os.environ, env, clear=True):
                    metadata = judge_metadata()
                Path(env['FINAL_RESULTS_FILE']).write_text(''.join(json.dumps({'model': command[-1], 'dataset': d, 'score': 70, 'recheck': metadata}) + '\n' for d in batch.DATASETS))
                return 0
            argv = ['batch', str(config.parent)] + ([] if mode == 'corrected' else ['--judge-prompt-mode', mode])
            with patch.object(sys, 'argv', argv), patch.object(batch.subprocess, 'call', side_effect=emit), contextlib.redirect_stdout(io.StringIO()) as stdout:
                batch.main()
            self.assertIn(f'Judge prompt: {mode}', stdout.getvalue())
            directory = next((self.root / 'evaluation_batches').glob(f'math_qwen3_32b_{mode}_*'))
            manifest = json.loads((directory / 'manifest.json').read_text())
            self.assertEqual(manifest['judge']['prompt_mode'], mode)
            self.assertIn(manifest['judge']['prompt_version'], (directory / 'summary.md').read_text())
            copy = Path(manifest['models'][0]['checkpoint_results_dir'])
            self.assertEqual(json.loads((copy / 'evaluation.json').read_text())['judge'], manifest['judge'])
            self.assertIn(f'Judge prompt: {mode}', (copy / 'summary.md').read_text())
            # A record from the other mode must not yield a valid score/average.
            other = dict(manifest, judge=dict(batch.JUDGE, **prompts.prompt_metadata('rzero-original' if mode == 'corrected' else 'corrected')))
            self.assertEqual(batch.summarize(directory, other)[0][2], 'invalid_results')
            with self.assertRaisesRegex(FileExistsError, 'another judge'):
                batch.copy_to_checkpoints(directory, other, [[1, 'solver', 'complete']])

    def test_nonmath_rejects_math_only_option(self):
        with patch.object(sys, 'argv', ['batch', '--suite', 'nonmath', '--judge-prompt-mode', 'rzero-original']), patch.object(batch.subprocess, 'call') as call, self.assertRaises(SystemExit):
            batch.main()
        call.assert_not_called()
