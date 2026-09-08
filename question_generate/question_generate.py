import vllm
import torch
from transformers import AutoTokenizer
import argparse
from typing import List
from vllm.outputs import RequestOutput
from evaluation.datasets_loader import get_dataset_handler
import json
import regex as re
import os
STORAGE_PATH = os.getenv("STORAGE_PATH")

def extract_boxed(text):
    results, i = [], 0
    prefix = r'\boxed{'
    plen = len(prefix)

    while True:
        start = text.find(prefix, i)
        if start == -1:
            break   # no more \boxed{…}

        j = start + plen
        depth = 1
        while j < len(text) and depth:
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
            j += 1

        results.append(text[start + plen : j - 1])
        i = j

    return results

def get_response_mask(response_ids, eos_token_id, dtype):
    batch_size, seq_len = response_ids.shape
    mask = torch.ones((batch_size, seq_len), dtype=dtype)
    for i in range(batch_size):
        for j in range(seq_len):
            if response_ids[i][j] == eos_token_id:
                mask[i][j:] = 0
                break
    return mask

def main(args):
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        # gpu_memory_utilization=0.8,
        seed=int(args.suffix),
    )
    dataset_handler = get_dataset_handler("math")
    questions, answers = dataset_handler.load_data()
    question = questions[0]
    answer = answers[0]
    chat = [
        {
            "role": "system",
            "content": (
                "You are an expert competition-math problem setter.\n"
                "FIRST, in your private scratch-pad, think step-by-step to design a brand-new, non-trivial problem. "
                "The problem could come from any field of mathematics, including but not limited to algebra, geometry, number theory, combinatorics, prealgebra, probability, statistics, and calculus. "
                "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
                "Avoid re-using textbook clichés or famous contest problems.\n"
                "THEN, without revealing any of your private thoughts, output **exactly** the following two blocks:\n\n"
                "<question>\n"
                "{The full problem statement on one or more lines}\n"
                "</question>\n\n"
                r"\boxed{final_answer}"
                "\n\n"
                "Do NOT output anything else—no explanations, no extra markup."
            )
        },
        {
            "role": "user",
            "content": (
                "Generate one new, challenging reasoning question now. "
                "Remember to format the output exactly as instructed."
            )
        }
    ]

    if tokenizer.chat_template:
        prompt = tokenizer.apply_chat_template(
            chat, 
            tokenize=False,
            add_generation_prompt=True, 
            add_special_tokens=True
        )
    else:
        prompt = "system: " + chat[0]["content"] + '\n' + "user: " + chat[1]["content"]
    sample_params = vllm.SamplingParams(
        max_tokens=4096,
        temperature=1.0,
        top_p=0.95,
        n=1,
        stop_token_ids=[tokenizer.eos_token_id],
    )

    domains = None
    prompts = [prompt] * args.num_samples
    if os.getenv("VALIDITY_RZERO_ENABLED", "0") == "1" and os.getenv("VALIDITY_RZERO_DOMAIN_MODE", "none") == "balanced_v1":
        from methods.validity_rzero.domain_curriculum.core import messages, phase_b_domains
        domains = phase_b_domains(args.num_samples, int(os.environ["QUESTION_NUM_SHARDS"]),
                                  int(args.suffix), int(os.getenv("VALIDITY_RZERO_DOMAIN_SEED", "43")), args.save_name)
        prompts = []
        for domain in domains:
            domain_chat = messages(domain)
            if tokenizer.chat_template:
                prompts.append(tokenizer.apply_chat_template(domain_chat, tokenize=False,
                    add_generation_prompt=True, add_special_tokens=True))
            else:
                prompts.append("system: " + domain_chat[0]["content"] + '\n' + "user: " + domain_chat[1]["content"])
    completions: List[RequestOutput] = model.generate(prompts, sampling_params=sample_params)
    results=[]
    for completion in completions:
        response = completion.outputs[0].text
        try:
            questions = re.findall(r"<question>(.*?)</question>", response, re.DOTALL)
            answers = extract_boxed(response)

            if questions and answers:
                question = questions[-1].strip()
                answer = answers[-1].strip()
                results.append({"question": question, "answer": answer, "score": 0})
            else:
                results.append({"question": response, "answer": "", "score": -1})
        except:
            results.append({"question": response, "answer": "", "score": -1})
    if domains is not None:
        assert len(results) == len(domains)
        for row, domain in zip(results, domains):
            row["domain"] = domain
    with open(f"{STORAGE_PATH}/generated_question/{args.save_name}_{args.suffix}.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-4B")
    parser.add_argument("--num_samples", type=int, default=1250, help="Number of samples to generate")
    parser.add_argument("--suffix", type=str, default="", help="Suffix to add to the output file")
    parser.add_argument("--save_name", type=str, default="", help="")
    args = parser.parse_args()

    main(args) 