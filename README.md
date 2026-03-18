# sanger-tol/tollongc

[![GitHub Actions CI Status](https://github.com/sanger-tol/tollongc/actions/workflows/nf-test.yml/badge.svg)](https://github.com/sanger-tol/tollongc/actions/workflows/nf-test.yml)
[![GitHub Actions Linting Status](https://github.com/sanger-tol/tollongc/actions/workflows/linting.yml/badge.svg)](https://github.com/sanger-tol/tollongc/actions/workflows/linting.yml)[![Cite with Zenodo](http://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-1073c8?labelColor=000000)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![nf-test](https://img.shields.io/badge/unit_tests-nf--test-337ab7.svg)](https://www.nf-test.com)

[![Nextflow](https://img.shields.io/badge/version-%E2%89%A524.10.5-green?style=flat&logo=nextflow&logoColor=white&color=%230DC09D&link=https%3A%2F%2Fnextflow.io)](https://www.nextflow.io/)
[![nf-core template version](https://img.shields.io/badge/nf--core_template-3.3.2-green?style=flat&logo=nfcore&logoColor=white&color=%2324B064&link=https%3A%2F%2Fnf-co.re)](https://github.com/nf-core/tools/releases/tag/3.3.2)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/sanger-tol/tollongc)

## Introduction

**sanger-tol/tollongc** is a Nextflow pipeline for processing CIFI/Pore-C chromatin conformation capture data from long-read sequencing. It converts raw reads into pairwise genomic contacts and generates contact matrices in multiple formats for downstream analysis and visualization.

The pipeline:

- **Digests** concatemer reads at restriction sites (optional) or aligns raw reads directly
- **Aligns** fragments to a reference genome with minimap2
- **Annotates** fragments and extracts pairwise contacts using pairtools parse2
- **Optionally restricts** contacts to restriction fragments (pairtools restrict)
- **Converts** pairs to cool, mcool, and pretext formats for visualization

### Pipeline overview

1. **Digest** (optional) — Split concatemers at restriction sites (NlaIII, DpnII, etc.)
2. **Align** — Minimap2 index and alignment
3. **Annotate** — Group fragments by read, assign fragment IDs
4. **Parse** — pairtools parse2: BAM → pairs format
5. **Restrict** (optional) — pairtools restrict: filter to restriction fragments
6. **Convert** — pairs → cool/mcool (cooler) and pretext (PretextMap)

## Usage

> [!NOTE]
> If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how to set-up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline) with `-profile test` before running the workflow on actual data.

### Input

Prepare a samplesheet with your input data:

`samplesheet.csv`:

```csv
sample,fastq_1,fastq_2
SAMPLE1,reads1.fastq.gz,
SAMPLE2,reads2.fastq.gz,
```

- `sample`: Sample identifier
- `fastq_1`: Path to FASTQ file (single-end reads)
- `fastq_2`: Optional, for paired-end (leave empty for Long-C)

### Running the pipeline

```bash
nextflow run sanger-tol/tollongc \
   -profile <docker/singularity/conda> \
   --input samplesheet.csv \
   --outdir <OUTDIR>
```

### Main parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input` | Path to samplesheet CSV | Required |
| `--outdir` | Output directory | Required |
| `--skip_digest` | Skip restriction digest, align raw reads | `false` |
| `--cutter` | Restriction enzyme (NlaIII, DpnII, HindIII, etc.) | `NlaIII` |
| `--restrict_fragments` | Restrict pairs to restriction fragments | `true` |
| `--cool` | Generate cool contact matrix | `true` |
| `--cool_bin_size` | Bin size for cool file (bp) | `10000` |
| `--mcool` | Generate multi-resolution mcool | `false` |
| `--mcool_resolutions` | Resolutions for mcool | `1000,2000,5000,...` |
| `--pretext` | Generate pretext file for PretextView | `true` |

### Output

| Output | Description |
|--------|-------------|
| `bam/` | Annotated BAM with fragment IDs |
| `pairs/` | 4DN pairs format (restricted or unrestricted) |
| `cool/` | Cool contact matrix (single resolution) |
| `mcool/` | Multi-resolution cool (if `--mcool`) |
| `pretext/` | Pretext format for PretextView visualization |

> [!WARNING]
> Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see [docs](https://nf-co.re/docs/usage/getting_started/configuration#custom-configuration-files).

## Credits

sanger-tol/tollongc was originally written by yumisims.

We thank the following people for their extensive assistance in the development of this pipeline:

<!-- TODO nf-core: If applicable, make list of people who have also contributed -->

## Contributions and Support

If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

## Citations

<!-- TODO nf-core: Add citation for pipeline after first release. Uncomment lines below and update Zenodo doi and badge at the top of this file. -->
<!-- If you use sanger-tol/tollongc for your analysis, please cite it using the following doi: [10.5281/zenodo.XXXXXX](https://doi.org/10.5281/zenodo.XXXXXX) -->

<!-- TODO nf-core: Add bibliography of tools and data used in your pipeline -->

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/main/LICENSE).

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
