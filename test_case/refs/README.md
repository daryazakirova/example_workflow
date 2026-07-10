# Demo reference materials

**`panel_region.fa`** — real GRCh38 sequence for two regions of the cardiomyopathy panel,
extracted from the source server's `hg38.fa` (read-only `samtools faidx` region query, no
patient data touched):

| Contig | Real GRCh38 coordinates | Gene | Length |
|---|---|---|---|
| `demo_chr11_MYBPC3` | chr11:47,330,407-47,353,702 (+1kb flank) | MYBPC3 | 23,296 bp |
| `demo_chr14_MYH7` | chr14:23,411,741-23,436,660 (+1kb flank) | MYH7 | 24,920 bp |

Contigs are renamed and re-numbered from position 1 (i.e. this is **not** a real chromosome —
it's a small, self-contained "mini genome" for the demo) so the whole test case stays under a
few hundred KB and runs in seconds, with no download required.

**`clinvar_panel_subset.vcf`** — a hand-built, single-variant VCF (not a raw ClinVar download)
containing just the fields the pipeline needs for one real, publicly documented pathogenic
variant, translated into this mini-genome's local coordinates:

| | Real-world (GRCh38) | This demo (`panel_region.fa` coordinates) |
|---|---|---|
| Variant | `NC_000011.10:g.47342698G>A` | `demo_chr11_MYBPC3:12292 G>A` |
| Gene / HGVS | MYBPC3 `NM_000256.3:c.1504C>T` (p.Arg502Trp) | same variant, same gene |
| ClinVar | [VCV000042540](https://www.ncbi.nlm.nih.gov/clinvar/variation/VCV000042540.4), Pathogenic | `CLNSIG=Pathogenic` |
| dbSNP | rs375882485 | `ID=rs375882485` |
| Condition | Hypertrophic cardiomyopathy | `CLNDN=Hypertrophic_cardiomyopathy` |

This is the most common recurrent MYBPC3 mutation in hypertrophic cardiomyopathy (Niimura et
al., *NEJM* 1998; Alders et al., *Circ Res* 2010) — chosen specifically because it's real,
well-published, and unambiguous, so the demo's "pathogenic hit" in `case1` is a genuine,
citable example rather than a made-up variant.

For a real (non-demo) run, point `CLINVAR_VCF` at the full public ClinVar VCF instead:
`https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz`

## Regenerating `panel_region.fa`

```bash
samtools faidx /path/to/hg38.fa chr11:47330407-47353702 chr14:23411741-23436660 \
  | sed 's/^>chr11.*/>demo_chr11_MYBPC3/; s/^>chr14.*/>demo_chr14_MYH7/' \
  > panel_region.fa
```
