# tollongc Pipeline Flowchart

```mermaid
flowchart TB
    subgraph Input
        A[("Samplesheet\n(sample, fastq_1, fastq_2)")]
        B[("Reference FASTA")]
    end

    subgraph Init["PIPELINE_INITIALISATION"]
        A --> C[Validate & Parse Samplesheet]
        C --> D[("longc_reads\nchannel")]
    end

    subgraph LONGC["LONGC Subworkflow"]
        D --> E{skip_digest?}
        B --> F[MINIMAP2_INDEX]
        
        E -->|No| G[SEQKIT_FX2TAB]
        E -->|Yes| H[("ch_reads_for_align\n(raw reads)")]
        
        G --> I[DIGEST_READS]
        I --> J[SEQKIT_TAB2FX]
        J --> H
        
        H --> K[MINIMAP2_ALIGN]
        F --> K
        
        K --> L[ANNOTATE_FRAG]
        L --> M[PAIRTOOLS_PARSE2]
        
        M --> N{restrict_fragments?}
        M --> P
        M --> Q
        B --> O[CREATE_RESTRICTION_BED]
        O --> P[PAIRTOOLS_RESTRICT]
        
        N -->|Yes| P
        N -->|No| Q
        P --> Q[("ch_pairs_final")]
        
        subgraph Optional["Optional Outputs"]
            B --> R[SAMTOOLS_FAIDX]
            Q --> S{cool?}
            Q --> T{pretext?}
            
            S -->|Yes| U[COOLER_CLOAD_PAIRS]
            U --> V{mcool?}
            V -->|Yes| W[COOLER_ZOOMIFY]
            
            T -->|Yes| X[PRETEXTMAP]
        end
    end

    subgraph Output["Outputs"]
        L --> O1[("BAM")]
        Q --> O2[("Pairs")]
        U --> O3[("Cool")]
        W --> O4[("mCool")]
        X --> O5[("Pretext")]
    end

    subgraph Completion["PIPELINE_COMPLETION"]
        O1 --> Z[Email / Summary]
        O2 --> Z
        O3 --> Z
        O4 --> Z
        O5 --> Z
    end
```

## Simplified Linear View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           tollongc Pipeline                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Input                    Digest (if !skip_digest)           Alignment
  ─────                    ────────────────────────            ─────────
  Samplesheet     ──►      SEQKIT_FX2TAB                     MINIMAP2_INDEX
  Reference       ──►      DIGEST_READS              ──►     MINIMAP2_ALIGN
                           SEQKIT_TAB2FX                     ANNOTATE_FRAG

  Pairs Processing         Restrict (optional)                Optional Outputs
  ─────────────────       ──────────────────                 ────────────────
  PAIRTOOLS_PARSE2  ──►    PAIRTOOLS_RESTRICT        ──►     COOLER_CLOAD_PAIRS
  (BAM → pairs)           (if restrict_fragments)            COOLER_ZOOMIFY
                                                             PRETEXTMAP

  Outputs: BAM | Pairs | Cool | mCool | Pretext
```

## Process Summary

| Step | Process | Input | Output |
|------|---------|-------|--------|
| 1 | SEQKIT_FX2TAB | FASTQ | Tabular (name, seq, qual) |
| 2 | DIGEST_READS | Tabular + cutter | Digested tabular |
| 3 | SEQKIT_TAB2FX | Digested tabular | FASTQ |
| 4 | MINIMAP2_INDEX | Reference FASTA | Index |
| 5 | MINIMAP2_ALIGN | Reads + Index | BAM |
| 6 | ANNOTATE_FRAG | BAM | Annotated BAM |
| 7 | PAIRTOOLS_PARSE2 | BAM + reference | Pairs |
| 8 | CREATE_RESTRICTION_BED | Reference + cutter | BED |
| 9 | PAIRTOOLS_RESTRICT | Pairs + BED | Restricted pairs |
| 10 | COOLER_CLOAD_PAIRS | Pairs + reference | Cool |
| 11 | COOLER_ZOOMIFY | Cool | mCool |
| 12 | PRETEXTMAP | Pairs | Pretext |
