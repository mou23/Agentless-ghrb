#!/bin/bash
#SBATCH --job-name=agentless-ghrb
#SBATCH --output=agentless-ghrb3.log
#SBATCH --error=agentless-ghrb3.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=5-00:00:00
#SBATCH --mem=64GB
#SBATCH --account=malek_lab
set -euo pipefail

module load python/3.10.2
# ======================
# Config
# ======================
REPO_LOCATION="$TMPDIR/ghrb"
echo "Preparing working dir at: $REPO_LOCATION"
mkdir -p "$REPO_LOCATION"

echo "Copying XML files from ../sample to $REPO_LOCATION..."
cp -v ../sample/*.xml "$REPO_LOCATION/"

echo "Downloading repositories into $REPO_LOCATION..."
python download_repo.py "$REPO_LOCATION"

RESULTS_DIR="results"

# ======================
# Timer
# ======================
START_TIME=$(date +%s)


# ======================
# Main Loop
# ======================
for dataset in Apktool assertj checkstyle dubbo fastjson gson jackson-core jackson-databind jackson-dataformat-xml jsoup nacos openapi-generator retrofit rocketmq seata sslcontext-kickstart # 
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
