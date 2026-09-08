"""Write the sequential, already shuffled Questioner schedule before GPU training."""
import argparse
from pathlib import Path
from .core import training_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--batch-size', type=int, required=True)
    parser.add_argument('--steps', type=int, required=True)
    parser.add_argument('--seed', type=int, default=43)
    parser.add_argument('--context', required=True)
    args = parser.parse_args()
    from datasets import Dataset
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = training_rows(args.batch_size, args.steps, args.seed, args.context)
    Dataset.from_list(rows).to_parquet(str(path))
    print(f'Domain curriculum: {len(rows)} prompts, {args.steps} balanced batches, seed={args.seed}')


if __name__ == '__main__':
    main()
