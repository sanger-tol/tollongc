process PAIRTOOLS_PARSE2 {
    tag "$meta.id"
    label 'process_medium'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pairtools:1.0.2--py39h2a9f597_0' :
        'biocontainers/pairtools:1.0.2--py39h2a9f597_0' }"

    input:
    tuple val(meta), path(bam)
    path fasta

    output:
    tuple val(meta), path("*.pairs.gz"), emit: pairs
    tuple val(meta), path("*.stats.txt"), emit: stats, optional: true
    path "versions.yml"                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: '--drop-sam --drop-seq --expand --add-pair-index'
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    samtools faidx ${fasta}
    pairtools parse2 \\
        --output-stats ${prefix}.stats.txt \\
        -c ${fasta}.fai \\
        --single-end \\
        --readid-transform 'readID.split(":")[0]' \\
        ${args} \\
        ${bam} | gzip -c > ${prefix}.pairs.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        pairtools: \$(pairtools --version | tr '\\n' ',' | sed 's/.*pairtools.*version //' | sed 's/,\$/\\n/')
    END_VERSIONS
    """
}
