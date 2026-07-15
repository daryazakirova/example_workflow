#!/bin/bash
# Replaces DRAGEN's --enable-map-align-output / --enable-sort / --enable-duplicate-marking
# / --enable-bam-indexing with: bwa mem -> samtools sort -> samtools markdup -> samtools index.
#
# Usage: 02_align.sh <sample_id> <R1.fastq.gz> <R2.fastq.gz>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/00_config.sh"

sample_id="$1"
r1="$2"
r2="$3"

bam_raw="$TMP_DIR/${sample_id}.raw.bam"
bam_sorted="$TMP_DIR/${sample_id}.sorted.bam"
bam_final="$OUT_DIR/${sample_id}.markdup.bam"

log "[$sample_id] fastp QC/trim"
fastp \
  -i "$r1" -I "$r2" \
  -o "$TMP_DIR/${sample_id}.trim_R1.fastq.gz" -O "$TMP_DIR/${sample_id}.trim_R2.fastq.gz" \
  --json "$OUT_DIR/${sample_id}.fastp.json" --html "$OUT_DIR/${sample_id}.fastp.html" \
  --thread "$THREADS" --quiet

log "[$sample_id] bwa mem alignment"
bwa mem -t "$THREADS" \
  -R "@RG\tID:${sample_id}\tSM:${sample_id}\tPL:ILLUMINA\tLB:${sample_id}" \
  "$REF_FASTA" \
  "$TMP_DIR/${sample_id}.trim_R1.fastq.gz" "$TMP_DIR/${sample_id}.trim_R2.fastq.gz" \
  | samtools view -@ "$THREADS" -b -o "$bam_raw" -

log "[$sample_id] fixmate (required before markdup)"
samtools fixmate -m -@ "$THREADS" "$bam_raw" "$TMP_DIR/${sample_id}.fixmate.bam"
mv "$TMP_DIR/${sample_id}.fixmate.bam" "$bam_raw"
log "[$sample_id] sort"
samtools sort -@ "$THREADS" -o "$bam_sorted" "$bam_raw"

log "[$sample_id] mark duplicates"
samtools markdup -@ "$THREADS" "$bam_sorted" "$bam_final"

log "[$sample_id] index"
samtools index -@ "$THREADS" "$bam_final"

rm -f "$bam_raw" "$bam_sorted"
log "[$sample_id] alignment complete -> $bam_final"
