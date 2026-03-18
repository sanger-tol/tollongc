process DIGEST_READS {
    tag "$meta.id"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"

    input:
    tuple val(meta), path(tabular)
    val cutter    // restriction enzyme name, e.g. 'NlaIII'

    output:
    tuple val(meta), path("*.tsv.gz"), emit: digested_tabular

    when:
    task.ext.when == null || task.ext.when

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    printf 'placeholder\\tN\\t!\\n' | gzip -c > ${prefix}.tsv.gz
    """

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def args = task.ext.args ?: ''
    def tab_list = tabular instanceof List ? tabular : [ tabular ]
    def tab_arg = tab_list.join(' ')
    """
    zcat ${tab_arg} | \\
    python ${projectDir}/bin/digest_reads.py --cutter ${cutter} --min-len 10 ${args} | \\
    gzip -c > ${prefix}.tsv.gz
    """
}
