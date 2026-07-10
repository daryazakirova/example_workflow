(function () {
  "use strict";

  const STORAGE_KEY = "variant-pipeline-guide-settings";

  const DEFAULTS = {
    refFasta: "test_case/refs/panel_region.fa",
    clinvarVcf: "test_case/refs/clinvar_panel_subset.vcf.gz",
    panelGenes: "panels/cardiomyopathy/cardiomyopathy_genes.txt",
    panelBed: "panels/cardiomyopathy/cardiomyopathy_genes_grch38.bed",
    panelName: "Cardiomyopathy (demo)",
    snpeffDb: "GRCh38.mane.1.2.ensembl",
    sampleId: "case1",
    sampleType: "case",
    r1Fastq: "test_case/fastq/case1_R1.fastq.gz",
    r2Fastq: "test_case/fastq/case1_R2.fastq.gz",
    threads: "8",
    outDir: "test_case/results",
    tmpDir: "test_case/results/tmp",
    manifest: "test_case/samples.tsv",
    caller: "bcftools",
  };

  let settings = { ...DEFAULTS };

  function loadSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        settings = { ...DEFAULTS, ...JSON.parse(raw) };
      }
    } catch (_) {
      settings = { ...DEFAULTS };
    }
  }

  function saveSettings() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }

  function readForm() {
    document.querySelectorAll("[data-setting]").forEach((el) => {
      const key = el.dataset.setting;
      settings[key] = el.value;
    });
    saveSettings();
  }

  function writeForm() {
    document.querySelectorAll("[data-setting]").forEach((el) => {
      const key = el.dataset.setting;
      if (settings[key] !== undefined) {
        el.value = settings[key];
      }
    });
  }

  function commonExports(s) {
    return `# Shared configuration (export before each stage, or source once)
export REF_FASTA="${s.refFasta}"
export CLINVAR_VCF="${s.clinvarVcf}"
export PANEL_GENES="${s.panelGenes}"
export PANEL_BED="${s.panelBed}"
export PANEL_NAME="${s.panelName}"
export SNPEFF_DB="${s.snpeffDb}"
export THREADS=${s.threads}
export OUT_DIR="${s.outDir}"
export TMP_DIR="${s.tmpDir}"`;
  }

  const STAGE_TEMPLATES = {
    setup: () =>
      `# One-time: create the conda environment
conda env create -f envs/environment.yml
conda activate variant-pipeline

# Optional: verify tools are on PATH
bwa && samtools && bcftools && python3 --version`,

    prepareReference: (s) =>
      `${commonExports(s)}

# Build BWA index, .fai, GATK dict, and tabix-index ClinVar (run once per reference)
pipeline/01_prepare_reference.sh`,

    align: (s) =>
      `${commonExports(s)}

# QC (fastp) -> bwa mem -> sort -> markdup -> index
pipeline/02_align.sh ${s.sampleId} ${s.r1Fastq} ${s.r2Fastq}`,

    callVariants: (s) =>
      `${commonExports(s)}

# Primary: bcftools mpileup + call. Secondary cross-check: GATK4 HaplotypeCaller.
pipeline/03_call_variants.sh ${s.sampleId}`,

    annotate: (s) =>
      `${commonExports(s)}

# snpEff (if DB installed) + ClinVar via bcftools annotate; optional VEP cross-check
pipeline/04_annotate.sh ${s.sampleId} ${s.caller}`,

    filterPathogenic: (s) =>
      `# Extract ClinVar Pathogenic / Likely pathogenic variants to JSONL
python3 pipeline/05_filter_pathogenic.py \\
  "${s.outDir}/${s.sampleId}.${s.caller}.annotated.vcf.gz" \\
  "${s.sampleId}" \\
  "${s.sampleType}" \\
  "${s.outDir}/${s.sampleId}.${s.sampleType}.pathogenic.jsonl"`,

    generateReport: (s) =>
      `# Interactive HTML clinical report for one sample
python3 pipeline/07_generate_report.py \\
  "${s.outDir}/${s.sampleId}.${s.caller}.annotated.vcf.gz" \\
  "${s.sampleId}" \\
  "${s.panelGenes}" \\
  "${s.outDir}/${s.sampleId}.report.html" \\
  "${s.panelName}"`,

    aggregate: (s) =>
      `# After all samples are processed: case vs control summary
python3 pipeline/06_aggregate_case_control.py \\
  "${s.outDir}/*.pathogenic.jsonl" \\
  "${s.outDir}/aggregated_pathogenic_variants.json"`,

    fullRun: (s) =>
      `${commonExports(s)}

# Manifest format (tab-separated, no header):
#   sample_id  case|control  R1.fastq.gz  R2.fastq.gz
pipeline/run_pipeline.sh ${s.manifest}`,
  };

  function renderBlock(id, text) {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = text;
    }
  }

  function renderAll() {
    readForm();
    const s = settings;
    renderBlock("code-setup", STAGE_TEMPLATES.setup());
    renderBlock("code-prepare", STAGE_TEMPLATES.prepareReference(s));
    renderBlock("code-align", STAGE_TEMPLATES.align(s));
    renderBlock("code-call", STAGE_TEMPLATES.callVariants(s));
    renderBlock("code-annotate", STAGE_TEMPLATES.annotate(s));
    renderBlock("code-filter", STAGE_TEMPLATES.filterPathogenic(s));
    renderBlock("code-report", STAGE_TEMPLATES.generateReport(s));
    renderBlock("code-aggregate", STAGE_TEMPLATES.aggregate(s));
    renderBlock("code-fullrun", STAGE_TEMPLATES.fullRun(s));
  }

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    const orig = btn.textContent;
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = orig;
      btn.classList.remove("copied");
    }, 1500);
  }

  function initCopyButtons() {
    document.querySelectorAll(".copy-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const block = btn.closest(".code-block");
        const pre = block && block.querySelector("pre");
        if (pre) {
          copyText(pre.textContent, btn);
        }
      });
    });
  }

  function initSettings() {
    writeForm();
    document.querySelectorAll("[data-setting]").forEach((el) => {
      el.addEventListener("input", renderAll);
      el.addEventListener("change", renderAll);
    });
    document.getElementById("reset-settings")?.addEventListener("click", () => {
      settings = { ...DEFAULTS };
      writeForm();
      saveSettings();
      renderAll();
    });
    document.getElementById("demo-settings")?.addEventListener("click", () => {
      settings = { ...DEFAULTS };
      writeForm();
      saveSettings();
      renderAll();
    });
  }

  function initMermaid() {
    if (typeof mermaid !== "undefined") {
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    }
  }

  loadSettings();
  initSettings();
  renderAll();
  initCopyButtons();
  initMermaid();
})();
