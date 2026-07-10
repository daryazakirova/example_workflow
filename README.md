# example_workflow — DRAGEN-free cardiomyopathy variant-calling pipeline

A CPU-only, license-free reconstruction of a whole-genome germline variant-calling and
clinical-reporting pipeline that was originally built around an Illumina DRAGEN
FPGA-accelerated server. This repository documents the original pipeline, provides a drop-in
open-source replacement, and ships a small, fully synthetic technical demo you can run on a
laptop in minutes.

**No real patient data, sample identifiers, or licensed reference data are included anywhere
in this repository.** See [`docs/`](docs/) for details.

## Why this exists

The original pipeline used Illumina DRAGEN (FPGA bitstream + a data-processing subscription)
to go from paired-end WGS FASTQ to annotated, clinically-filtered variant calls for a panel of
26 cardiomyopathy/channelopathy genes, comparing patient ("case") samples against unaffected
("control") samples. When the DRAGEN subscription lapsed, the pipeline needed a CPU-only
replacement that keeps the same inputs/outputs and clinical logic without requiring
specialized hardware or a paid license.

## What's here

| Path | Contents |
|---|---|
| [`docs/ORIGINAL_DRAGEN_PIPELINE.md`](docs/ORIGINAL_DRAGEN_PIPELINE.md) | Reconstruction of the original FPGA-accelerated pipeline, as run in production |
| [`docs/DRAGEN_TO_OSS_MAPPING.md`](docs/DRAGEN_TO_OSS_MAPPING.md) | Stage-by-stage table mapping each DRAGEN feature to its open-source replacement |
| [`panel/`](panel/) | The 26-gene cardiomyopathy/channelopathy panel (unchanged from the original pipeline) |
| [`envs/environment.yml`](envs/environment.yml) | Conda environment: bwa, samtools, bcftools, GATK4, snpEff, fastp/fastqc |
| [`pipeline/`](pipeline/) | The replacement pipeline: align → call variants (bcftools + GATK4) → annotate (snpEff/VEP + ClinVar) → filter pathogenic calls → case/control aggregate → HTML report |
| [`test_case/`](test_case/) | A small, synthetic, shareable 2-sample demo (1 case + 1 control) that runs the whole pipeline end-to-end |

## Quick start (synthetic demo)

```bash
conda env create -f envs/environment.yml
conda activate cardio-pipeline

cd test_case
./run_demo.sh
python check_demo.py results
```

This aligns two small synthetic samples against a ~48kb slice of real GRCh38 sequence (MYBPC3
+ MYH7), calls variants, annotates against a real published ClinVar pathogenic variant, and
generates an interactive HTML clinical report per sample — end to end in well under a minute,
no FPGA or license required. See [`test_case/README.md`](test_case/README.md) for details.

## Running on real data

```bash
export REF_FASTA=/path/to/hg38.fa
export CLINVAR_VCF=/path/to/clinvar_grch38.vcf.gz   # https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/
pipeline/run_pipeline.sh my_cohort_manifest.tsv
```

`my_cohort_manifest.tsv` is tab-separated: `sample_id  case|control  R1.fastq.gz  R2.fastq.gz`
(see `test_case/samples.tsv` for the format).

## Known differences vs. the original DRAGEN pipeline

- No equivalent to DRAGEN's proprietary pangenome graph-reference mode is provided (linear
  GRCh38 only) — see `docs/DRAGEN_TO_OSS_MAPPING.md`.
- Exact variant calls and QC metrics will differ slightly from DRAGEN's output, as expected
  when comparing any two independently-implemented aligners/callers. Cross-validation against
  the original pipeline's pathogenic-variant calls on real samples (kept on the source
  infrastructure, never included here) is a recommended follow-up before relying on this
  pipeline for anything beyond technical demonstration.
- Annotation uses independently-downloaded public resources (ClinVar, and optionally
  snpEff/VEP), not Illumina's licensed Nirvana data bundle.

## License

See [`LICENSE`](LICENSE). The cardiomyopathy gene panel, pipeline logic, and clinical filtering
rules are provided as-is for technical/educational purposes and are **not validated for
clinical use**.
