process DIGEST_READS {
    tag "$meta.id"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"

    input:
    tuple val(meta), path(reads)
    val cutter    // restriction enzyme name, e.g. 'NlaIII'

    output:
    tuple val(meta), path("*.fastq.gz"), emit: digested_reads

    when:
    task.ext.when == null || task.ext.when

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    printf '@placeholder\\nN\\n+\\n!\\n' | gzip -c > ${prefix}.fastq.gz
    """

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def args = task.ext.args ?: ''
    def reads_list = reads instanceof List ? reads : [ reads ]
    def reads_arg = reads_list.join(' ')
    def input_cmd = reads_list.any { it.name.endsWith('.bam') || it.name.endsWith('.cram') } ?
        "samtools fastq -@ ${task.cpus} ${reads_arg}" : "seqkit seq ${reads_arg}"
    """
    ${input_cmd} | \\
    seqkit fx2tab -n -i -q | \\
    python ${projectDir}/bin/digest_reads.py --cutter ${cutter} --min-len 10 ${args} | \\
    seqkit tab2fx -o ${prefix}.fastq.gz
    """
}
