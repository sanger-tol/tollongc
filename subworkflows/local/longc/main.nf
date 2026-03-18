//
// Subworkflow: Long-C alignment (optional digest + minimap2 index + align + annotate fragments)
//

include { DIGEST_READS   } from '../../../modules/local/digest_reads/main'
include { MINIMAP2_INDEX } from '../../../modules/nf-core/minimap2/index/main'
include { MINIMAP2_ALIGN } from '../../../modules/nf-core/minimap2/align/main'
include { ANNOTATE_FRAG  } from '../../../modules/local/annotate_frag/main'
include { TO_CONTACTS    } from '../../../modules/local/to_contacts/main'

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
    // Extract pairwise contacts to 4DN pairs format
    //
    TO_CONTACTS ( ANNOTATE_FRAG.out.bam )

    emit:
    bam            = ANNOTATE_FRAG.out.bam
    pairs          = TO_CONTACTS.out.pairs
    versions_minimap2_index = MINIMAP2_INDEX.out.versions_minimap2
    versions_minimap2_align = MINIMAP2_ALIGN.out.versions_minimap2

}
