//
// Subworkflow: Long-C alignment (optional digest + minimap2 index + align + annotate fragments)
//

include { DIGEST_READS            } from '../../../modules/local/digest_reads/main'
include { CREATE_RESTRICTION_BED  } from '../../../modules/local/create_restriction_bed/main'
include { MINIMAP2_INDEX          } from '../../../modules/nf-core/minimap2/index/main'
include { MINIMAP2_ALIGN          } from '../../../modules/nf-core/minimap2/align/main'
include { ANNOTATE_FRAG           } from '../../../modules/local/annotate_frag/main'
include { PAIRTOOLS_PARSE2        } from '../../../modules/nf-core/pairtools/parse2/main'
include { PAIRTOOLS_RESTRICT      } from '../../../modules/nf-core/pairtools/restrict/main'
include { SAMTOOLS_FAIDX         } from '../../../modules/local/samtools_faidx/main'
include { COOLER_CLOAD_PAIRS     } from '../../../modules/local/cooler_cload_pairs/main'
include { COOLER_ZOOMIFY         } from '../../../modules/nf-core/cooler/zoomify/main'
include { PRETEXTMAP             } from '../../../modules/nf-core/pretextmap/main'

workflow LONGC {

    take:
    reference       // channel: tuple(meta, path(fasta))
    longc_reads     // channel: tuple(meta, path(reads))

    main:

    //
    // Optionally digest reads (split concatemers at restriction sites)
    // When skip_digest=true, align raw reads directly, the output is a BAM file with the original read names
    //
    if (params.skip_digest) {
        ch_reads_for_align = longc_reads
    } else {
        DIGEST_READS ( longc_reads, Channel.of(params.cutter) )
        ch_reads_for_align = DIGEST_READS.out.digested_reads
    }

    //
    // Index reference FASTA with minimap2
    //
    MINIMAP2_INDEX ( reference )

    //
    // Align reads to indexed reference (pair each sample with reference)
    //
    ch_ref_index = MINIMAP2_INDEX.out.index
    ch_for_align = ch_reads_for_align.combine(ch_ref_index)
    MINIMAP2_ALIGN (
        ch_for_align.map { it -> it[0] },
        ch_for_align.map { it -> it[1] },
        true,   // bam_format
        'bai',  // bam_index_extension
        false,  // cigar_paf_format
        false   // cigar_bam
    )

    //
    // Annotate aligned fragments: group by read, filter, order, assign fragment IDs
    //
    ch_align_bam = MINIMAP2_ALIGN.out.bam.join(MINIMAP2_ALIGN.out.index)
    ANNOTATE_FRAG ( ch_align_bam )

    //
    // Convert BAM to pairs (pairtools parse2) — first step after annotate_frag
    //
    ch_ref_fasta = reference.map { it -> it[1] }.first()
    ch_bam_for_parse = ANNOTATE_FRAG.out.bam.map { meta, bam, bai -> [meta, bam] }
    PAIRTOOLS_PARSE2 ( ch_bam_for_parse.combine(ch_ref_fasta) )

    //
    // Optionally restrict pairs to restriction fragments (cooler digest → pairtools restrict)
    //
    use_restrict = !params.skip_digest && params.restrict_fragments
    ch_fragments = use_restrict
        ? CREATE_RESTRICTION_BED(reference, Channel.of(params.cutter)).out.bed
        : Channel.empty()
    ch_pairs_for_restrict = use_restrict
        ? PAIRTOOLS_PARSE2.out.pairs.combine(ch_fragments.map { meta, bed -> bed })
        : Channel.empty()
    ch_pairs_final = use_restrict
        ? PAIRTOOLS_RESTRICT(ch_pairs_for_restrict).out.restrict
        : PAIRTOOLS_PARSE2.out.pairs

    //
    // Convert pairs to cool and pretext (optional)
    //
    SAMTOOLS_FAIDX ( reference )

    use_cool = params.cool || params.mcool
    if (use_cool) {
        COOLER_CLOAD_PAIRS (
            ch_pairs_final
                .combine(ch_ref_fasta)
                .map { meta, pairs, fasta -> [meta, pairs, fasta, params.cool_bin_size] }
        )
    }
    if (params.mcool && params.cool) {
        COOLER_ZOOMIFY ( COOLER_CLOAD_PAIRS.out.cool )
    }
    if (params.pretext) {
        PRETEXTMAP ( ch_pairs_final.combine(SAMTOOLS_FAIDX.out.fasta_fai) )
    }

    emit:
    bam            = ANNOTATE_FRAG.out.bam
    pairs          = ch_pairs_final
    cool           = use_cool ? COOLER_CLOAD_PAIRS.out.cool : Channel.empty()
    mcool          = (params.mcool && params.cool) ? COOLER_ZOOMIFY.out.mcool : Channel.empty()
    pretext        = params.pretext ? PRETEXTMAP.out.pretext : Channel.empty()
    versions_minimap2_index = MINIMAP2_INDEX.out.versions_minimap2
    versions_minimap2_align = MINIMAP2_ALIGN.out.versions_minimap2

}
