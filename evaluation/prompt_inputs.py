"""Keep checkpoint chat templates and avoid re-adding Llama/Octo BOS in vLLM."""


def validate_checkpoint_template(tokenizer):
    # Octo Hybrid uses the Llama BOS. Trained checkpoints persist their template;
    # silently falling back to a different wrapper would change their protocol.
    if tokenizer.bos_token == '<|begin_of_text|>':
        if not tokenizer.chat_template:
            raise ValueError(
                'Octo/Llama evaluation requires the checkpoint chat_template. '
                'Use the complete trained checkpoint tokenizer; no template is substituted.'
            )
        print('Evaluation input: saved checkpoint template; explicit token IDs; '
              'add_special_tokens=False', flush=True)


def generation_inputs(prompts, tokenizer):
    if tokenizer.bos_token != '<|begin_of_text|>':
        return prompts  # Preserve the established Qwen evaluation path.
    if not tokenizer.chat_template:
        raise ValueError('Missing checkpoint chat_template; refusing a different evaluation wrapper')
    inputs = []
    for prompt in prompts:
        ids = tokenizer.encode(prompt, add_special_tokens=False)
        # The saved training wrapper must supply exactly one leading BOS.
        if not ids or ids[0] != tokenizer.bos_token_id:
            raise ValueError('Saved Octo/Llama template did not produce a leading BOS')
        if len(ids) > 1 and ids[1] == tokenizer.bos_token_id:
            raise ValueError('Saved Octo/Llama template produced duplicate leading BOS tokens')
        inputs.append({'prompt_token_ids': ids})
    return inputs

