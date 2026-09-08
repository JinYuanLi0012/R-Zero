"""Deterministic hierarchical prompt allocation; no model or reward dependencies."""
import hashlib
import random

DOMAINS = (
    ("Arithmetic and Quantitative Relations", (
        "Ratios, proportions, and percentages", "Rates, time, work, and unit relations",
        "Averages, mixtures, and quantity balances")),
    ("Algebraic Relations", (
        "Equations and systems of equations", "Algebraic expressions and identities",
        "Inequalities and bounds", "Polynomial, rational, and radical relations")),
    ("Functions and Sequences", (
        "Functions, composition, and inverse relations", "Sequences, recurrences, and series",
        "Exponential, logarithmic, and trigonometric relations")),
    ("Geometry", (
        "Triangles, polygons, lengths, and areas", "Circles, chords, tangency, and cyclic figures",
        "Coordinate and locus geometry", "Solid and spatial geometry")),
    ("Number Theory and Integer Structures", (
        "Divisibility, factors, primes, GCD, and LCM", "Congruences and modular arithmetic",
        "Integer equations and integer constraints", "Digits, bases, and number representations")),
    ("Combinatorics and Discrete Structures", (
        "Selections, permutations, and arrangements", "Distributions, partitions, and occupancy",
        "Paths, grids, graphs, and finite configurations")),
    ("Probability", (
        "Finite probability and sample spaces", "Conditional and sequential probability",
        "Expected values and random quantities")),
    ("Calculus and Applied Quantitative Mathematics", (
        "Limits, derivatives, and optimization", "Integrals and accumulated quantities",
        "Differential equations and changing systems", "Scientific formulas, units, and coupled quantities")),
)

SYSTEM = (
    "You are an expert competition-math problem setter.\n"
    "FIRST, in your private scratch-pad, think step-by-step to design a brand-new, non-trivial problem. "
    "The problem must belong to the following mathematical domain:\n{domain}\n"
    "The solution must centrally require concepts or reasoning from this domain. "
    "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
    "Avoid re-using textbook clichés or famous contest problems.\n"
    "THEN, without revealing any of your private thoughts, output **exactly** the following two blocks:\n\n"
    "<question>\n{The full problem statement on one or more lines}\n</question>\n\n"
    r"\boxed{final_answer}"
    "\n\nDo NOT output anything else—no explanations, no extra markup."
)
USER = ("Generate one new, challenging reasoning question now. "
        "Remember to format the output exactly as instructed.")


def messages(domain):
    return [{"role": "system", "content": SYSTEM.replace("{domain}", domain)},
            {"role": "user", "content": USER}]


def balanced_domains(count, seed=43, block=0, context=""):
    """Balance parents first, then leaves; rotate remainder recipients each block."""
    if count < 0:
        raise ValueError("count must be nonnegative")
    rows = []
    for parent_index, (parent, leaves) in enumerate(DOMAINS):
        parent_count = count // 8 + int((parent_index - block) % 8 < count % 8)
        for leaf_index, leaf in enumerate(leaves):
            n = parent_count // len(leaves) + int(
                (leaf_index - block) % len(leaves) < parent_count % len(leaves))
            rows.extend([f"{parent} → {leaf}"] * n)
    digest = hashlib.sha256(f"{seed}:{block}:{context}".encode()).digest()
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(rows)
    return rows


def training_rows(batch_size, steps, seed, context):
    if batch_size < 1 or steps < 1:
        raise ValueError("batch size and steps must be positive")
    return [{"problem": domain, "answer": "", "domain": domain,
             "domain_prompt_id": f"{context}:{step}:{index}"}
            for step in range(steps)
            for index, domain in enumerate(balanced_domains(batch_size, seed, step, context))]


def phase_b_domains(per_shard, shards, shard, seed, context):
    if shards < 1 or not 0 <= shard < shards:
        raise ValueError("invalid shard topology")
    plan = balanced_domains(per_shard * shards, seed, context=context)
    return plan[shard * per_shard:(shard + 1) * per_shard]
