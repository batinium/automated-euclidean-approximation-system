#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PURGE_RESULTS=0
WITH_VISUALS=1
EXTRA_EXPERIMENTS=0
JUSTIFICATION_EXPERIMENTS=0

usage() {
  cat <<'USAGE'
Usage: bash scripts/rerun_all.sh [options]

Options:
  --purge-results   Archive existing results/ into results_archive/results_<timestamp> before rerun
  --no-visuals      Skip scripts/visualize_search.py
  --extra-experiments  Run additional robustness/fairness experiments after core grid
  --justification-experiments  Run compact parameter-sensitivity runs to justify fixed defaults
  -h, --help        Show this help

Notes:
  - Run from an environment where project deps are installed.
  - This script runs all experiments sequentially.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge-results)
      PURGE_RESULTS=1
      shift
      ;;
    --no-visuals)
      WITH_VISUALS=0
      shift
      ;;
    --extra-experiments)
      EXTRA_EXPERIMENTS=1
      shift
      ;;
    --justification-experiments)
      JUSTIFICATION_EXPERIMENTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_cmd() {
  log "RUN: $*"
  "$@"
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found in PATH" >&2
  exit 1
fi

mkdir -p results results_archive

if [[ "$PURGE_RESULTS" -eq 1 ]]; then
  TS="$(date +%Y%m%d-%H%M%S)"
  if [[ -d results ]] && [[ -n "$(find results -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)" ]]; then
    ARCHIVE_DIR="results_archive/results_${TS}"
    log "Archiving existing results/ to ${ARCHIVE_DIR}"
    mv results "$ARCHIVE_DIR"
    mkdir -p results
  else
    log "results/ is already empty; nothing to archive"
  fi
fi

log "Stage 1/6: RQ2 baseline (beam)"
run_cmd python3 scripts/run_search.py \
  --mode beam \
  --n 7 11 13 \
  --max_depth 3 \
  --max_nodes 15 \
  --beam_width 2000 \
  --dps 80 \
  --run_name beam_n7-11-13_d3_nodes15_bw2000

log "Stage 2/6: RQ2 baseline (field)"
run_cmd python3 scripts/run_search.py \
  --mode field \
  --n 7 11 13 \
  --max_depth 3 \
  --max_height 20 \
  --max_radicand 30 \
  --beam_width 2000 \
  --dps 80 \
  --run_name field_n7-11-13_d3_h20_r30_bw2000

log "Stage 3/6: RQ1 height sweep (depth=2)"
for H in 8 12 16 24 32 48; do
  run_cmd python3 scripts/run_search.py \
    --mode field \
    --n 7 11 13 \
    --max_depth 2 \
    --max_height "$H" \
    --max_radicand 30 \
    --beam_width 2000 \
    --dps 80 \
    --run_name "field_n7-11-13_d2_h${H}_r30_bw2000"
done

log "Stage 4/6: RQ1 depth sweep (height=32)"
for D in 0 1 2 3 4; do
  run_cmd python3 scripts/run_search.py \
    --mode field \
    --n 7 11 13 \
    --max_depth "$D" \
    --max_height 32 \
    --max_radicand 30 \
    --beam_width 2000 \
    --dps 80 \
    --run_name "field_n7-11-13_d${D}_h32_r30_bw2000"
done

log "Stage 5/6: Saturation control (height=64)"
run_cmd python3 scripts/run_search.py \
  --mode field \
  --n 7 11 13 \
  --max_depth 4 \
  --max_height 64 \
  --max_radicand 30 \
  --beam_width 2000 \
  --dps 80 \
  --run_name field_n7-11-13_d4_h64_r30_bw2000

if [[ "$EXTRA_EXPERIMENTS" -eq 1 ]]; then
  log "Extra experiments: stronger beam + higher-height field"

  run_cmd python3 scripts/run_search.py \
    --mode beam \
    --n 7 11 13 \
    --max_depth 4 \
    --max_nodes 30 \
    --beam_width 5000 \
    --dps 80 \
    --run_name beam_n7-11-13_d4_nodes30_bw5000

  run_cmd python3 scripts/run_search.py \
    --mode field \
    --n 7 11 13 \
    --max_depth 4 \
    --max_height 96 \
    --max_radicand 30 \
    --beam_width 2000 \
    --dps 80 \
    --run_name field_n7-11-13_d4_h96_r30_bw2000
fi

if [[ "$JUSTIFICATION_EXPERIMENTS" -eq 1 ]]; then
  log "Justification experiments: beam_width / radicand / dps / beam max_nodes sweeps"

  # 1) Beam width sensitivity (field mode)
  for BW in 1000 2000 5000; do
    run_cmd python3 scripts/run_search.py \
      --mode field \
      --n 7 11 13 \
      --max_depth 3 \
      --max_height 20 \
      --max_radicand 30 \
      --beam_width "$BW" \
      --dps 80 \
      --run_name "justif_field_bw${BW}_d3_h20_r30_dps80"
  done

  # 2) Radicand bound sensitivity (field mode)
  for R in 20 30 40; do
    run_cmd python3 scripts/run_search.py \
      --mode field \
      --n 7 11 13 \
      --max_depth 3 \
      --max_height 20 \
      --max_radicand "$R" \
      --beam_width 2000 \
      --dps 80 \
      --run_name "justif_field_r${R}_d3_h20_bw2000_dps80"
  done

  # 3) Precision sensitivity (field mode)
  for P in 60 80 120; do
    run_cmd python3 scripts/run_search.py \
      --mode field \
      --n 7 11 13 \
      --max_depth 3 \
      --max_height 20 \
      --max_radicand 30 \
      --beam_width 2000 \
      --dps "$P" \
      --run_name "justif_field_dps${P}_d3_h20_r30_bw2000"
  done

  # 4) Beam max_nodes sensitivity (beam mode)
  for NODES in 15 25 35; do
    run_cmd python3 scripts/run_search.py \
      --mode beam \
      --n 7 11 13 \
      --max_depth 3 \
      --max_nodes "$NODES" \
      --beam_width 2000 \
      --dps 80 \
      --run_name "justif_beam_nodes${NODES}_d3_bw2000_dps80"
  done
fi

log "Stage 6/6: Regenerate plots + analysis"
run_cmd python3 scripts/plot_results.py --root results --all-runs
run_cmd python3 scripts/plot_results.py --root results --multi-run-grid
run_cmd python3 scripts/analyse_scaling.py

if [[ "$WITH_VISUALS" -eq 1 ]]; then
  log "Generating paper visuals"
  run_cmd python3 scripts/visualize_search.py --root results --mode architecture
  run_cmd python3 scripts/visualize_search.py --root results --mode expr-tree --n 7 --depth 3 --rank 1
  run_cmd python3 scripts/visualize_search.py --root results --mode expr-tree --n 11 --depth 3 --rank 1
  run_cmd python3 scripts/visualize_search.py --root results --mode expr-tree --n 13 --depth 3 --rank 1
  run_cmd python3 scripts/visualize_search.py --root results --mode heatmap --n 7 --m 2 --max-height 32
  run_cmd python3 scripts/visualize_search.py --root results --mode heatmap --n 11 --m 2 --max-height 32
  run_cmd python3 scripts/visualize_search.py --root results --mode layers --n 7
  run_cmd python3 scripts/visualize_search.py --root results --mode layers --n 11
  run_cmd python3 scripts/visualize_search.py --root results --mode layers --n 13
else
  log "Skipping optional paper visuals (--no-visuals)"
fi

log "Done. Key outputs:"
log "  - results/multi_run_summary.csv"
log "  - results/multi_run_error_vs_depth.png"
log "  - results/analysis/*"
