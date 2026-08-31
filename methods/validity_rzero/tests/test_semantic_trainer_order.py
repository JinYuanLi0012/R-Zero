from pathlib import Path


def test_semantic_barrier_separates_log_probs_from_reward_and_actor_update():
    source = (Path(__file__).parents[3] / "verl" / "trainer" / "ray_trainer.py").read_text(
        encoding="utf-8"
    )
    reward_launch = source.index("reward_ref = self.reward_fn.compute_reward.remote(batch)")
    old_log_probs = source.index("old_log_probs = self.actor_rollout_wg.compute_log_probs(batch)", reward_launch)
    ref_log_probs = source.index("ref_log_probs = self.ref_policy_wg.compute_ref_log_probs(batch)", old_log_probs)
    ready = source.index("signal_ready(semantic_barrier)", ref_log_probs)
    reward_join = source.index("reward_tensor, reward_metrics = ray.get(reward_ref)", ready)
    actor_update = source.index("actor_output = self.actor_rollout_wg.update_actor(batch)", reward_join)
    assert reward_launch < old_log_probs < ref_log_probs < ready < reward_join < actor_update
