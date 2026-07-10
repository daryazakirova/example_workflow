#!/bin/bash
# Shared configuration for all pipeline scripts.
# Override any of these with environment variables before calling run_pipeline.sh.

set -euo pipefail

: "${REF_FASTA:=$PWD/refs/hg38_panel.fa}"          # reference FASTA (whole genome, or panel-restricted for the demo)
: "${CLINVAR_VCF:=$PWD/refs/clinvar_grch38.vcf.gz}" # public ClinVar VCF, GRCh38
: "${SNPEFF_DB:=GRCh38.mane.1.2.ensembl}"           # snpEff database name
: "${PANEL_BED:=$PWD/panel/cardiomyopathy_genes_grch38.bed}"
: "${PANEL_GENES:=$PWD/panel/cardiomyopathy_genes.txt}"
: "${THREADS:=8}"
: "${OUT_DIR:=$PWD/results}"
: "${TMP_DIR:=$OUT_DIR/tmp}"

mkdir -p "$OUT_DIR" "$TMP_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}
