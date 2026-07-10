#!/usr/bin/env python3
"""Sanity-check the demo pipeline output: case1 must show the spiked MYBPC3 pathogenic
variant, control1 must not. Used both interactively and by the CI workflow.

Usage: check_demo.py <results_dir>
"""
import json
import sys

EXPECTED_CONTIG = "demo_chr11_mybpc3"
EXPECTED_POS = 12292


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
    agg_path = f"{results_dir}/aggregated_pathogenic_variants.json"

    with open(agg_path) as fh:
        aggregated = json.load(fh)

    hits = [
        v for v in aggregated
        if v["chr"].lower() == EXPECTED_CONTIG and v["pos"] == EXPECTED_POS
    ]

    assert hits, f"Expected pathogenic variant at {EXPECTED_CONTIG}:{EXPECTED_POS} not found in {agg_path}"
    variant = hits[0]

    assert "case1" in variant["case_samples"], f"case1 should carry the pathogenic variant: {variant}"
    assert "control1" not in variant["control_samples"], f"control1 should NOT carry the pathogenic variant: {variant}"
    assert "pathogenic" in variant["clinvar_significance"].lower(), f"Expected Pathogenic significance: {variant}"

    print("OK: case1 carries the spiked MYBPC3 p.Arg502Trp pathogenic variant; control1 does not.")
    print(json.dumps(variant, indent=2))


if __name__ == "__main__":
    main()
