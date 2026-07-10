#!/usr/bin/env python3
"""Generate a small, fully synthetic paired-end FASTQ test case (no real patient data).

Reads are simulated from `refs/panel_region.fa`, which contains real GRCh38 sequence for two
cardiomyopathy panel genes (MYBPC3, MYH7), extracted from the reference on the source server
(coordinates documented in refs/README.md). No real sequencing reads, sample identifiers, or
patient information are used anywhere in this test case.

To make the demo clinically meaningful, one sample ("case1") is simulated as a heterozygous
carrier of a real, publicly documented pathogenic ClinVar variant:

    MYBPC3 NM_000256.3:c.1504C>T (p.Arg502Trp) -- ClinVar VCV000042540, dbSNP rs375882485
    GRCh38 chr11:47,342,698 G>A -- the most common recurrent HCM-causing MYBPC3 variant
    (Niimura et al. NEJM 1998; Alders et al. Circ Res 2010)

The other sample ("control1") is simulated from the unmodified reference (no variant).

This is a teaching/technical example only -- not derived from, and not representative of, any
real patient's sequencing data.

Usage:
    simulate_reads.py --ref refs/panel_region.fa --out-dir fastq --seed 42
"""
import argparse
import gzip
import random
import sys

# Position of the spiked pathogenic variant within the demo_chr11_MYBPC3 contig
# (0-based), corresponding to real GRCh38 chr11:47,342,698 G>A.
MYBPC3_VARIANT_CONTIG = "demo_chr11_MYBPC3"
MYBPC3_VARIANT_OFFSET_0BASED = 12291
MYBPC3_VARIANT_REF = "G"
MYBPC3_VARIANT_ALT = "A"

READ_LEN = 150
INSERT_MEAN = 400
INSERT_SD = 40
BASE_ERROR_RATE = 0.001
COVERAGE = 40

BASES = "ACGT"
COMPLEMENT = str.maketrans("ACGTN", "TGCAN")


def load_fasta(path):
    seqs = {}
    header = None
    cur = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if header:
                    seqs[header] = "".join(cur)
                header = line[1:].split()[0]
                cur = []
            else:
                cur.append(line)
        if header:
            seqs[header] = "".join(cur)
    return seqs


def revcomp(seq):
    return seq.translate(COMPLEMENT)[::-1]


def apply_errors(seq, rng, error_rate):
    if error_rate <= 0:
        return seq
    seq = list(seq)
    for i in range(len(seq)):
        if rng.random() < error_rate:
            seq[i] = rng.choice([b for b in BASES if b != seq[i]])
    return "".join(seq)


def qual_string(length, phred=35):
    return chr(phred + 33) * length


def simulate_contig(name, seq, coverage, rng, error_rate):
    """Yield (r1_seq, r2_seq) pairs sampled uniformly across the contig."""
    n_pairs = max(1, (len(seq) * coverage) // (2 * READ_LEN))
    for _ in range(n_pairs):
        insert = max(READ_LEN * 2 + 10, int(rng.gauss(INSERT_MEAN, INSERT_SD)))
        if insert >= len(seq):
            continue
        start = rng.randint(0, len(seq) - insert)
        frag = seq[start:start + insert]
        r1 = apply_errors(frag[:READ_LEN], rng, error_rate)
        r2 = apply_errors(revcomp(frag[-READ_LEN:]), rng, error_rate)
        yield name, start, r1, r2


def write_fastq_pair(pairs, out_r1, out_r2, sample_id):
    with gzip.open(out_r1, "wt") as f1, gzip.open(out_r2, "wt") as f2:
        for i, (contig, start, r1, r2) in enumerate(pairs):
            read_name = f"{sample_id}:{contig}:{start}:{i}"
            f1.write(f"@{read_name} 1\n{r1}\n+\n{qual_string(len(r1))}\n")
            f2.write(f"@{read_name} 2\n{r2}\n+\n{qual_string(len(r2))}\n")


def build_haplotypes(seqs):
    wt = dict(seqs)
    mut = dict(seqs)
    contig = mut[MYBPC3_VARIANT_CONTIG]
    assert contig[MYBPC3_VARIANT_OFFSET_0BASED] == MYBPC3_VARIANT_REF, (
        "Reference base mismatch at the spiked variant position -- "
        "refs/panel_region.fa does not match the expected GRCh38 sequence."
    )
    mut[MYBPC3_VARIANT_CONTIG] = (
        contig[:MYBPC3_VARIANT_OFFSET_0BASED]
        + MYBPC3_VARIANT_ALT
        + contig[MYBPC3_VARIANT_OFFSET_0BASED + 1:]
    )
    return wt, mut


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="refs/panel_region.fa")
    ap.add_argument("--out-dir", default="fastq")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--coverage", type=int, default=COVERAGE)
    args = ap.parse_args()

    import os
    os.makedirs(args.out_dir, exist_ok=True)

    seqs = load_fasta(args.ref)
    wt_seqs, mut_seqs = build_haplotypes(seqs)

    rng = random.Random(args.seed)

    # control1: homozygous wild-type at both loci
    control_pairs = []
    for name, seq in wt_seqs.items():
        control_pairs.extend(simulate_contig(name, seq, args.coverage, rng, BASE_ERROR_RATE))
    rng.shuffle(control_pairs)
    write_fastq_pair(control_pairs,
                      f"{args.out_dir}/control1_R1.fastq.gz",
                      f"{args.out_dir}/control1_R2.fastq.gz",
                      "control1")
    print(f"control1: {len(control_pairs)} read pairs (homozygous reference)", file=sys.stderr)

    # case1: heterozygous carrier -- half the MYBPC3 coverage from the mutant haplotype,
    # half from wild-type; MYH7 is unaffected (wild-type only) for this demo.
    case_pairs = []
    half_cov = max(1, args.coverage // 2)
    case_pairs.extend(simulate_contig(MYBPC3_VARIANT_CONTIG, wt_seqs[MYBPC3_VARIANT_CONTIG],
                                       half_cov, rng, BASE_ERROR_RATE))
    case_pairs.extend(simulate_contig(MYBPC3_VARIANT_CONTIG, mut_seqs[MYBPC3_VARIANT_CONTIG],
                                       half_cov, rng, BASE_ERROR_RATE))
    case_pairs.extend(simulate_contig("demo_chr14_MYH7", wt_seqs["demo_chr14_MYH7"],
                                       args.coverage, rng, BASE_ERROR_RATE))
    rng.shuffle(case_pairs)
    write_fastq_pair(case_pairs,
                      f"{args.out_dir}/case1_R1.fastq.gz",
                      f"{args.out_dir}/case1_R2.fastq.gz",
                      "case1")
    print(f"case1: {len(case_pairs)} read pairs "
          f"(heterozygous MYBPC3 p.Arg502Trp carrier, simulated)", file=sys.stderr)


if __name__ == "__main__":
    main()
