#!/bin/bash
# One-time setup for the demo: bgzip + tabix-index the small ClinVar subset VCF.
# (Shipped as plain text since bgzip/tabix aren't always available on the machine
# authoring the repo; any Linux/macOS box with htslib installed can run this.)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

bgzip -f -k refs/clinvar_panel_subset.vcf
tabix -f -p vcf refs/clinvar_panel_subset.vcf.gz

echo "Demo reference materials ready: refs/panel_region.fa, refs/clinvar_panel_subset.vcf.gz"
