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


def test_final_validation_honors_semantic_skip_without_changing_step_validation():
    source = (Path(__file__).parents[3] / "verl" / "trainer" / "ray_trainer.py").read_text(
        encoding="utf-8"
    )
    step_validation = source.index("and self.config.trainer.val_freq > 0")
    final_section = source.index("# perform validation after training")
    skip_decision = source.index("should_skip_final_validation", final_section)
    guarded_final = source.index("if self.val_reward_fn is not None and not skip_final_validation", skip_decision)
    final_validate = source.index("val_metrics = self._validate()", guarded_final)
    assert step_validation < final_section < skip_decision < guarded_final < final_validate
