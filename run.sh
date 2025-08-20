#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# ======================
# Config
# ======================
REPO_LOCATION="../ghrb-dataset"
RESULTS_DIR="agentless-results"
LOG_FILE="run.log"

# ======================
# Setup logging
# ======================
# Redirect stdout and stderr to both console and log file
exec > >(tee -a "$LOG_FILE") 2>&1

# ======================
# Timer
# ======================
START_TIME=$(date +%s)

# Error handling: print dataset name on failure
trap 'echo "❌ Error occurred while processing dataset: $dataset"; \
      END_TIME=$(date +%s); \
      ELAPSED=$((END_TIME - START_TIME)); \
      echo "⏱️ Elapsed time before failure: $((ELAPSED / 60)) min $((ELAPSED % 60)) sec"; \
      exit 1' ERR

# ======================
# Main Loop
# ======================
for dataset in seata #Apktool assertj checkstyle dubbo fastjson gson jackson-core jackson-databind jackson-dataformat-xml jsoup nacos openapi-generator retrofit rocketmq seata sslcontext-kickstart
do
    echo "🚀 Processing dataset: $dataset"

    # 1. File-level localization
    python -m agentless.fl.localize \
        --file_level \
        --output_folder $RESULTS_DIR/file_level/$dataset \
        --num_threads 1 \
        --skip_existing \
        --repo_location "$REPO_LOCATION" \
        --dataset $dataset

    # 2. File-level localization (irrelevant)
    python -m agentless.fl.localize \
        --file_level \
        --irrelevant \
        --output_folder $RESULTS_DIR/file_level_irrelevant/$dataset \
        --num_threads 1 \
        --skip_existing \
        --repo_location "$REPO_LOCATION" \
        --dataset $dataset

    # 3. Retrieval
    python -m agentless.fl.retrieve \
        --index_type simple \
        --filter_type given_files \
        --filter_file $RESULTS_DIR/file_level_irrelevant/$dataset/loc_outputs.jsonl \
        --output_folder $RESULTS_DIR/retrieval_embedding/$dataset \
        --persist_dir embedding/simple/$dataset \
        --num_threads 1 \
        --repo_location "$REPO_LOCATION" \
        --dataset $dataset

    # 4. Combine results
    python -m agentless.fl.combine \
        --retrieval_loc_file $RESULTS_DIR/retrieval_embedding/$dataset/retrieve_locs.jsonl \
        --model_loc_file $RESULTS_DIR/file_level/$dataset/loc_outputs.jsonl \
        --top_n 10 \
        --output_folder $RESULTS_DIR/file_level_combined/$dataset

    echo "✅ Finished dataset: $dataset"
    echo "---------------------------------------"
done

# ======================
# Elapsed Time Report
# ======================
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "🎉 All datasets completed successfully!"
echo "⏱️ Total elapsed time: $((ELAPSED / 60)) min $((ELAPSED % 60)) sec"
