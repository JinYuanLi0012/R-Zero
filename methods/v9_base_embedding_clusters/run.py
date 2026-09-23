"""Fixed V9 sample: Qwen3-4B-Base hidden-state embeddings and clustering."""
import argparse
import collections
import csv
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import subprocess

import numpy as np
from sklearn.cluster import AgglomerativeClustering

HERE = pathlib.Path(__file__).resolve().parent
MODEL = 'Qwen/Qwen3-4B-Base'
SAMPLE_SHA = 'ce1a220b41a221d27a68efb0786e7d56f8ddad8654c72d10d29cd654da42a17f'
POOLING = 'final_hidden_state_masked_mean_float32_l2; no special tokens or chat template'


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_sample():
    path = HERE / 'data/sample_63.jsonl'
    if sha(path) != SAMPLE_SHA:
        raise ValueError('Bundled fixed sample changed; refusing a different experiment')
    rows = [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 63 and len({r['row_zero_based'] for r in rows}) == 63
    assert all(isinstance(r['question'], str) and r['question'].strip() for r in rows)
    assert [r['row_zero_based'] for r in rows] == sorted(r['row_zero_based'] for r in rows)
    return rows


def masked_mean(hidden, mask):
    # Same semantics as methods/novelty_pair_diagnostic/backends.py.
    import torch
    weights = mask.unsqueeze(-1).to(dtype=torch.float32)
    counts = weights.sum(dim=1)
    if (counts == 0).any():
        raise ValueError('empty token sequence')
    pooled = (hidden.float() * weights).sum(dim=1) / counts
    if not torch.isfinite(pooled).all() or (pooled.norm(dim=-1) == 0).any():
        raise ValueError('invalid embedding vector')
    return torch.nn.functional.normalize(pooled, p=2, dim=-1)


def embed(rows, args):
    import torch
    from transformers import AutoModel, AutoTokenizer
    from huggingface_hub import HfApi
    torch.manual_seed(20260922)
    model_path = pathlib.Path(args.model_path).expanduser() if args.model_path else None
    if model_path:
        if not model_path.is_dir() or args.revision:
            raise ValueError('--model-path must be a local Qwen3-4B-Base directory; do not combine with --revision')
        model_id = str(model_path.resolve())
        files = sorted(p for p in model_path.rglob('*') if p.is_file() and p.suffix in ('.json', '.safetensors', '.bin', '.txt', '.model', '.jinja'))
        if not any(p.suffix in ('.safetensors', '.bin') for p in files):
            raise ValueError('No checkpoint weights in local model directory')
        identity = dict(model=MODEL, local_path=model_id, local_hashes={str(p.relative_to(model_path)): sha(p) for p in files}, revision=None, local_checkpoint_identity='user-supplied Base checkpoint; architecture checked, training provenance not inferable from tensors')
    else:
        revision = HfApi().model_info(MODEL, revision=args.revision).sha
        model_id = MODEL
        identity = dict(model=MODEL, revision=revision)
    dtype = getattr(torch, args.dtype)
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=identity['revision'], padding_side='right')
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModel.from_pretrained(model_id, revision=identity['revision'], torch_dtype=dtype, attn_implementation='sdpa').to(args.device).eval()
    model.requires_grad_(False)
    if model.config.model_type != 'qwen3' or model.config.hidden_size != 2560 or model.config.num_hidden_layers != 36:
        raise ValueError('Expected Qwen3-4B-Base architecture (qwen3, hidden_size=2560, 36 layers)')
    limit = min(args.max_length, model.config.max_position_embeddings)
    vectors, lengths = [], []
    with torch.inference_mode():
        for start in range(0, len(rows), args.batch_size):
            batch = rows[start:start + args.batch_size]
            tokens = tokenizer([r['question'] for r in batch], add_special_tokens=False, truncation=False, padding=False)['input_ids']
            if any(not t or len(t) > limit for t in tokens):
                raise ValueError(f'Empty/overlong input (limit {limit}); no truncation: {[(r["id"], len(t)) for r, t in zip(batch, tokens)]}')
            encoded = tokenizer.pad({'input_ids': tokens}, padding=True, return_tensors='pt').to(args.device)
            outputs = model(**encoded, use_cache=False, return_dict=True)
            vectors.append(masked_mean(outputs.last_hidden_state, encoded['attention_mask']).cpu().numpy())
            lengths.extend(map(len, tokens))
            print(f'Embedded {start + len(batch)}/{len(rows)}', flush=True)
    return np.concatenate(vectors), dict(identity=identity, pooling=POOLING, token_counts=lengths, truncated=False, dtype=args.dtype, device=args.device, batch_size=args.batch_size, max_length=limit, attention='sdpa', seed=20260922)


def distance_matrix(vectors, n):
    vectors = np.asarray(vectors, dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[0] != n or vectors.shape[1] == 0 or not np.isfinite(vectors).all():
        raise ValueError('Invalid embedding array')
    norms = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(norms).all() or np.any(norms == 0):
        raise ValueError('Zero embedding')
    unit = vectors / norms[:, None]
    # Small fixed sample: explicit contraction also avoids platform BLAS warnings.
    similarities = np.einsum('ik,jk->ij', unit, unit, optimize=False)
    distances = np.clip(1.0 - similarities, 0.0, 2.0)
    distances = (distances + distances.T) / 2
    np.fill_diagonal(distances, 0)
    return distances


def cluster(vectors, threshold):
    distances = distance_matrix(vectors, len(vectors))
    raw = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold, metric='precomputed', linkage='average').fit_predict(distances)
    order = sorted(set(raw), key=lambda label: list(raw).index(label))
    ids = {label: f'E{i:03d}' for i, label in enumerate(order, 1)}
    return [ids[label] for label in raw], distances


def export(rows, labels, out, threshold):
    baseline = {r['id']: r for r in map(json.loads, (HERE / 'data/bleu_mapping.jsonl').read_text(encoding='utf-8').splitlines())}
    mapping = []
    for row, label in zip(rows, labels):
        assert baseline[row['id']]['question'] == row['question']
        mapping.append(dict(row, embedding_cluster=label, bleu_cluster=baseline[row['id']]['bleu_cluster']))
    (out / 'mapping.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in mapping), encoding='utf-8')
    counts = collections.Counter(labels)
    groups = [dict(cluster=label, count=count, percentage=100 * count / len(rows), members=[r['id'] for r in mapping if r['embedding_cluster'] == label]) for label, count in counts.items()]
    summary = dict(N=len(rows),K=len(groups),distance='1-cosine',linkage='average',distance_threshold=threshold,largest_cluster_count=max(counts.values()),largest_cluster_percentage=100*max(counts.values())/len(rows),bleu_K=len({r['bleu_cluster'] for r in mapping}),clusters=groups)
    write_json(out / 'summary.json', summary)
    with (out / 'cluster_sizes.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(['cluster','count','percentage'])
        w.writerows((g['cluster'],g['count'],g['percentage']) for g in groups)
    text = []
    for g in groups:
        text.append('=' * 80 + f'\n{g["cluster"]} | {g["count"]}/{len(rows)} | {g["percentage"]:.2f}%\n' + '=' * 80 + '\n\n')
        for r in mapping:
            if r['embedding_cluster'] == g['cluster']:
                text.append(f'----- {r["id"]} | source row (0-based) {r["row_zero_based"]} | BLEU {r["bleu_cluster"]} -----\n')
                text.extend([r['question'], '\n\n'])
    (out / 'clusters_original_questions.txt').write_text(''.join(text), encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'clusters'}, indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--distance-threshold', type=float, default=0.5)
    p.add_argument('--model-path', help='Optional local copy of Qwen3-4B-Base ONLY')
    p.add_argument('--revision', help='HF revision; resolves to immutable commit before loading')
    p.add_argument('--device', default='cuda')
    p.add_argument('--dtype', choices=['bfloat16','float16','float32'], default='bfloat16')
    p.add_argument('--batch-size', type=int, default=4)
    p.add_argument('--max-length', type=int, default=8192)
    p.add_argument('--reuse-embeddings', type=pathlib.Path, help='Completed output directory from this script; verify cache hashes and skip model loading')
    args = p.parse_args(argv)
    if not np.isfinite(args.distance_threshold) or not 0 < args.distance_threshold <= 2:
        p.error('distance threshold must be finite and in (0,2]')
    if args.batch_size < 1 or args.max_length < 1:
        p.error('batch-size and max-length must be positive')
    if args.reuse_embeddings and (args.model_path or args.revision):
        p.error('reuse selects recorded model identity; do not pass model options')
    rows = read_sample()
    if args.output.exists():
        p.error('output already exists; choose a fresh directory to avoid overwriting results')
    args.output.mkdir(parents=True)
    if args.reuse_embeddings:
        old = json.loads((args.reuse_embeddings / 'manifest.json').read_text())
        if old['sample_sha256'] != SAMPLE_SHA or old['embedding']['pooling'] != POOLING or old['embedding']['identity']['model'] != MODEL:
            raise ValueError('Cache model, sample or pooling differs')
        vecfile = args.reuse_embeddings / 'embeddings.npy'
        if sha(vecfile) != old['embeddings_sha256']:
            raise ValueError('Cached embeddings checksum mismatch')
        vectors = np.load(vecfile, allow_pickle=False)
        metadata = old['embedding']
    else:
        vectors, metadata = embed(rows, args)
    distance_matrix(vectors, len(rows))
    np.save(args.output / 'embeddings.npy', vectors)
    labels, dist = cluster(vectors, args.distance_threshold)
    np.save(args.output / 'cosine_distance.npy', dist)
    export(rows, labels, args.output, args.distance_threshold)
    versions = {}
    for name in ['torch','transformers','huggingface-hub','numpy','scikit-learn','scipy']:
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    try: commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=HERE, text=True).strip()
    except (subprocess.CalledProcessError,FileNotFoundError): commit = None
    write_json(args.output / 'manifest.json', dict(sample_sha256=SAMPLE_SHA,script_sha256=sha(__file__),git_commit=commit,embedding=metadata,embeddings_sha256=sha(args.output/'embeddings.npy'),threshold=args.distance_threshold,python=platform.python_version(),versions=versions,reused_from=str(args.reuse_embeddings) if args.reuse_embeddings else None))


if __name__ == '__main__':
    main()
