#!/bin/bash
set -e

Base_model=$1
Model_abbr=$2
echo "Model_abbr: $Model_abbr"
# Initialize first iteration with base model
bash scripts/questioner_train_penalty.sh  $Base_model $Base_model ${Model_abbr}_questioner_v1
bash scripts/solver_train.sh $Base_model ${STORAGE_PATH}/models/${Model_abbr}_questioner_v1/global_step_5/actor/huggingface ${Model_abbr}_solver_v1


for i in {2..5}; do
    prev=$((i-1))
    
    bash scripts/questioner_train_penalty.sh \
        ${STORAGE_PATH}/models/${Model_abbr}_solver_v${prev}/global_step_15/actor/huggingface \
        ${STORAGE_PATH}/models/${Model_abbr}_questioner_v${prev}/global_step_5/actor/huggingface \
        ${Model_abbr}_questioner_v${i}

    # Train solver
    bash scripts/solver_train.sh \
        ${STORAGE_PATH}/models/${Model_abbr}_solver_v${prev}/global_step_15/actor/huggingface \
        ${STORAGE_PATH}/models/${Model_abbr}_questioner_v${i}/global_step_5/actor/huggingface \
        ${Model_abbr}_solver_v${i}
done

bash evaluation/evaluate.bash $Base_model
