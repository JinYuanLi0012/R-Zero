"""CPU checks for GPU ownership, original reward composition, and ordered dispatch."""

from contextlib import ExitStack
from dataclasses import replace
import json
import os
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest
import requests

from methods.validity_rzero import reward_gpu_borrow as borrow
from methods.validity_rzero import service_handoff as handoff
from methods.validity_rzero.tests.test_service_handoff import config
from methods.validity_rzero.tests.test_questioner_diversity import _run_compute_score, _validity_result


@pytest.mark.parametrize('failure', [None, 'start', 'dispatch'])
def test_borrow_waits_then_releases_before_return_or_error(tmp_path, failure):
    service = config(tmp_path)
    events = []
    captured = {}
    baseline = {'0': [71], '1': [72]}  # live, offloaded trainer processes

    def start(extra):
        events.append('start')
        captured['extra'] = extra
        if failure == 'start':
            raise RuntimeError('start failed')

    def dispatch(data, ports, directory):
        events.append('dispatch')
        assert ports == (5000, 5001, 5002, 5003)
        if failure == 'dispatch':
            raise RuntimeError('dispatch failed')
        return data

    def release(gpus, timeout, allowed_pids):
        events.append('release')
        assert gpus == ('0', '1') and allowed_pids == baseline

    with patch.dict(os.environ, {
        'STORAGE_PATH': str(tmp_path), 'QUESTIONER_TRAIN_GPU_IDS': '0,1',
        'VALIDITY_RZERO_REWARD_PID_FILE': str(tmp_path / 'extra.pids'),
    }, clear=True), ExitStack() as stack:
        stack.enter_context(patch.object(borrow.SolverServiceConfig, 'from_environment', return_value=service))
        stack.enter_context(patch.object(borrow, 'wait_until_ready', side_effect=lambda _: events.append('ready') or 0))
        stack.enter_context(patch.object(borrow, 'gpu_compute_pids', return_value=baseline))
        stack.enter_context(patch.object(borrow, 'start_solver_services', side_effect=start))
        stack.enter_context(patch.object(borrow, 'dispatch_reward_shards', side_effect=dispatch))
        terminate = stack.enter_context(patch.object(borrow, 'terminate_recorded_process_groups', side_effect=lambda _: events.append('stop')))
        stack.enter_context(patch.object(borrow, 'wait_ports_closed', side_effect=lambda *_: events.append('ports')))
        stack.enter_context(patch.object(borrow, 'wait_gpus_released', side_effect=release))
        if failure:
            with pytest.raises(RuntimeError, match=f'{failure} failed'):
                borrow.generate_with_borrowed_gpus([{'question': 'q'}], ['ready.json'], 2, 5000)
        else:
            assert borrow.generate_with_borrowed_gpus([{'question': 'q'}], ['ready.json'], 2, 5000) == [{'question': 'q'}]
        terminate.assert_called_once_with(tmp_path / 'extra.pids')
    assert events == ['ready', 'start'] + ([] if failure == 'start' else ['dispatch']) + ['stop', 'ports', 'release']
    extra = captured['extra']
    assert extra.gpu_ids == ('0', '1') and extra.model_path == service.model_path
    assert extra.run_id == 'run-id_reward' and extra.pid_file != service.pid_file
    assert bool(list((tmp_path / 'temp_results').iterdir())) == bool(failure)


def test_bad_or_missing_barrier_never_starts_services(tmp_path):
    with patch.object(borrow, 'start_solver_services') as start:
        for barriers in (None, [], ['a', 'b'], ['', '']):
            with pytest.raises(RuntimeError, match='barrier'):
                borrow.generate_with_borrowed_gpus([], barriers, 2, 5000)
        start.assert_not_called()


def test_gpu_overlap_is_rejected_before_start(tmp_path, monkeypatch):
    monkeypatch.setenv('QUESTIONER_TRAIN_GPU_IDS', '0,2')
    with patch.object(borrow.SolverServiceConfig, 'from_environment', return_value=config(tmp_path)), \
         patch.object(borrow, 'start_solver_services') as start:
        with pytest.raises(ValueError, match='disjoint'):
            borrow.generate_with_borrowed_gpus([], ['ready'], 2, 5000)
        start.assert_not_called()


def test_aborted_barrier_never_starts_or_stops_any_services(tmp_path, monkeypatch):
    monkeypatch.setenv('QUESTIONER_TRAIN_GPU_IDS', '0,1')
    monkeypatch.setenv('VALIDITY_RZERO_REWARD_PID_FILE', str(tmp_path / 'extra.pids'))
    with patch.object(borrow.SolverServiceConfig, 'from_environment', return_value=config(tmp_path)), \
         patch.object(borrow, 'wait_until_ready', side_effect=RuntimeError('aborted')), \
         patch.object(borrow, 'start_solver_services') as start, \
         patch.object(borrow, 'terminate_recorded_process_groups') as stop:
        with pytest.raises(RuntimeError, match='aborted'):
            borrow.generate_with_borrowed_gpus([], ['ready'], 2, 5000)
        start.assert_not_called()
        stop.assert_not_called()


def test_dispatch_preserves_order_even_when_last_shard_finishes_first(tmp_path):
    final_done = Event()
    data = [{'question': str(i), 'answer': 'original'} for i in range(11)]
    data[2] = {'question': '', 'answer': ''}  # malformed candidate must retain its slot
    sizes = {}

    def get(url, params, timeout):
        path = Path(params['name'])
        shard = json.loads(path.read_text())
        sizes[path.stem] = len(shard)
        if ':5003/' in url:
            final_done.set()
        else:
            assert final_done.wait(timeout=5)
        rows = [dict(row, score=.3, answer='voted') for row in shard]
        path.with_name(path.stem + '_results.json').write_text(json.dumps(rows))
        response = requests.Response()
        response.status_code = 200
        return response

    with patch.object(borrow.requests, 'get', side_effect=get):
        rows = borrow.dispatch_reward_shards(data, (5000, 5001, 5002, 5003), tmp_path)
    assert [row['question'] for row in rows] == [row['question'] for row in data]
    assert sizes == {'shard_0': 3, 'shard_1': 3, 'shard_2': 3, 'shard_3': 2}


@pytest.mark.parametrize('fault', ['http', 'missing_row', 'wrong_question'])
def test_dispatch_rejects_failed_or_misaligned_results(tmp_path, fault):
    def get(url, params, timeout):
        path = Path(params['name'])
        rows = [] if fault == 'missing_row' else [{'question': 'wrong'}]
        path.with_name(path.stem + '_results.json').write_text(json.dumps(rows))
        response = requests.Response()
        response.status_code = 500 if fault == 'http' else 200
        return response
    with patch.object(borrow.requests, 'get', side_effect=get):
        with pytest.raises(requests.HTTPError if fault == 'http' else RuntimeError):
            borrow.dispatch_reward_shards([{'question': 'q'}], (5002,), tmp_path)


def test_start_uses_configured_extra_endpoints_not_inherited_permanent_pool(tmp_path):
    extra = replace(config(tmp_path), gpu_ids=('0', '1'), port_base=5002, pid_file=tmp_path / 'extra.pids')
    with patch.dict(os.environ, {'VLLM_GPU_IDS': '2,3', 'VLLM_PORT_BASE': '5000',
                                'QUESTIONER_VLLM_PID_FILE': str(tmp_path / 'permanent.pids')}), \
         patch.object(handoff.subprocess, 'run') as run, patch.object(handoff, 'wait_services_healthy'):
        handoff.start_solver_services(extra)
    env = run.call_args.kwargs['env']
    assert (env['VLLM_GPU_IDS'], env['VLLM_PORT_BASE'], env['QUESTIONER_VLLM_PID_FILE']) == ('0,1', '5002', str(extra.pid_file))


def test_release_allows_trainer_but_waits_for_vllm_children():
    baseline = {'0': [71], '1': [72]}
    with patch.object(handoff, 'gpu_compute_pids', side_effect=[{'0': [71, 999], '1': [72]}, baseline]) as query, \
         patch.object(handoff.time, 'sleep') as sleep:
        handoff.wait_gpus_released(('0', '1'), 10, allowed_pids=baseline)
    assert query.call_count == 2 and sleep.call_count == 1


def test_borrowing_keeps_novelty_and_invalid_reward_composition():
    results = [_validity_result(.4), _validity_result(.5 - 7/9, 'INVALID', 7)]
    novelty = [dict(novelty=0, same_count=1, compared_count=8, parse_failure_count=0)] * 2
    env = {'VALIDITY_RZERO_ENABLED': '1', 'VALIDITY_RZERO_DIVERSITY_MODE': 'semantic_novelty_gate'}
    original, _ = _run_compute_score(results, [], env, novelty_stats=novelty, ready_files=['ready'] * 2)
    with patch.object(borrow, 'generate_with_borrowed_gpus', return_value=results) as generate:
        accelerated, _ = _run_compute_score(results, [], dict(env, VALIDITY_RZERO_REWARD_BORROW_GPUS='1'),
                                             novelty_stats=novelty, ready_files=['ready'] * 2)
    assert accelerated == original
    assert [row['overall'] for row in accelerated] == [0, .5 - 7/9]
    assert generate.call_args.args[1:] == (['ready', 'ready'], 2, 5000)
