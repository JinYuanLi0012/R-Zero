"""Prompt/tokenizer adaptation for the Q/S backbone only; no reward changes."""
from pathlib import Path


def prepare_backbone_tokenizer(model, output, prompt):
    """Save tokenizer assets, never copy/change the source model's weights."""
    if prompt == 'native':
        return model
    if prompt != 'octothinker':
        raise ValueError(f'Unknown backbone prompt: {prompt}')
    from transformers import AutoConfig, AutoTokenizer

    config = AutoConfig.from_pretrained(model)
    tokenizer = AutoTokenizer.from_pretrained(model)
    if (config.model_type != 'llama' or tokenizer.bos_token_id != 128000
            or tokenizer.eos_token_id != 128001
            or tokenizer.bos_token != '<|begin_of_text|>'):
        raise ValueError('OctoThinker prompt requires the Llama OctoThinker Base tokenizer')
    tokenizer.chat_template = Path(__file__).with_name('octothinker_chat.jinja').read_text()
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(output)
    # AutoProcessor can inspect model_type before falling back to AutoTokenizer.
    config.save_pretrained(output)
    return str(output)


def inference_tokenizer_path(model, config, mode):
    if mode in {'generate', 'solve'} and config.get('backbone_prompt') == 'octothinker':
        return config['backbone_tokenizer']
    return model


def generation_inputs(prompts, tokenizer, config, mode):
    if mode in {'generate', 'solve'} and config.get('backbone_prompt') == 'octothinker':
        # The saved template already supplies BOS. Match training raw_prompt_ids.
        return [{'prompt_token_ids': tokenizer.encode(prompt, add_special_tokens=False)}
                for prompt in prompts]
    return prompts
