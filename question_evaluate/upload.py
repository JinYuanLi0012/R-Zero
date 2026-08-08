import json
import huggingface_hub
from datasets import Dataset, DatasetDict
from huggingface_hub import login
import argparse
import json
import os
from pathlib import Path
STORAGE_PATH = os.getenv("STORAGE_PATH")
HUGGINGFACENAME = os.getenv("HUGGINGFACENAME")
print(STORAGE_PATH)
with open('tokens.json', 'r') as f:
    token = json.load(f)['huggingface']
login(token=token)
parser = argparse.ArgumentParser()
parser.add_argument("--repo_name", type=str, default="")
parser.add_argument("--max_score", type=float, default=0.7)
parser.add_argument("--min_score", type=float, default=0.3)
parser.add_argument("--experiment_name", type=str, default="Qwen_Qwen3-4B-Base_all")
parser.add_argument("--num_shards", type=int, default=int(os.getenv("QUESTION_NUM_SHARDS", "4")))
parser.add_argument("--receipt", type=Path, default=None)
args = parser.parse_args()

datas= []
for i in range(args.num_shards):
    try:
        with open(f'{STORAGE_PATH}/generated_question/{args.experiment_name}_{i}_results.json', 'r') as f:
            data = json.load(f)
            datas.extend(data)
    except:
        print(f"File {args.experiment_name}_{i}_results.json not found")
        continue


for i in range(args.num_shards):
    try:
        os.remove(f'{STORAGE_PATH}/generated_question/{args.experiment_name}_{i}_results.json')
    except:
        print(f"File {args.experiment_name}_{i}_results.json not found")
        continue

scores = [data['score'] for data in datas]
#  print the distribution of scores
import matplotlib.pyplot as plt
plt.hist(scores, bins=11)
plt.savefig('scores_distribution.png')

#count the number  of score between 0.2 and 0.8 
if not args.repo_name == "":
    filtered_datas = [{'problem':data['question'],'answer':data['answer'],'score':data['score']} for data in datas if data['score'] >= args.min_score and data['score'] <= args.max_score and data['answer'] != '' and data['answer']!= 'None']
    print(len(filtered_datas))
    train_dataset = Dataset.from_list(filtered_datas)
    dataset_dict = {"train": train_dataset}
    config_name = f"{args.experiment_name}"
    dataset = DatasetDict(dataset_dict)
    dataset_id = f"{HUGGINGFACENAME}/{args.repo_name}"
    dataset.push_to_hub(dataset_id,private=True,config_name=config_name)
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_name(f"{args.receipt.name}.tmp-{os.getpid()}")
        temporary.write_text(json.dumps({
            "dataset_id": dataset_id,
            "config_name": config_name,
            "filtered_count": len(filtered_datas),
            "num_shards": args.num_shards,
            "min_score": args.min_score,
            "max_score": args.max_score,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, args.receipt)






