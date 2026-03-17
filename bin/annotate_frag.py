#!/usr/bin/env python3
"""
Copyright (c) 2024,2025 Genome Research Ltd.
@author: Yumi Sims, yy5@sanger.ac.uk
Annotate fragments in aligned BAM: group by read, filter, order, assign fragment IDs.

Usage:
    annotate_frag.py --input <bam> --output <bam> [options]

Example:
    annotate_frag.py --input aligned.bam --output annotated.bam --min-mapq 10
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from collections import defaultdict

try:
    import pysam
except ImportError:
    sys.exit("ERROR: pysam required. Install with: pip install pysam")


def parse_read_id(qname: str) -> tuple[str, int | None]:
    """Extract read_id and monomer_idx from query name. Returns (read_id, monomer_idx or None)."""
    if ":" in qname:
        parts = qname.rsplit(":", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0], int(parts[1])
    return qname, None


def main():
    parser = argparse.ArgumentParser(
        description="Annotate fragments in BAM: group by read, filter, order, assign fragment IDs"
    )
    parser.add_argument("--input", "-i", required=True, help="Input BAM (coordinate or name sorted)")
    parser.add_argument("--output", "-o", required=True, help="Output annotated BAM")
    parser.add_argument("--min-mapq", type=int, default=10, help="Minimum mapping quality for alignments [10]")
    parser.add_argument("--primary-only", action="store_true", default=True, help="Keep only primary alignments")
    parser.add_argument("--threads", type=int, default=1, help="Threads for BAM I/O")
    args = parser.parse_args()

    # 1. Read BAM and group alignments by read
    alns_by_read: dict[str, list] = defaultdict(list)
    with pysam.AlignmentFile(args.input, "rb", threads=args.threads) as bam_in:
        for aln in bam_in:
            if aln.is_unmapped:
                continue
            # 2. Filter alignments
            if args.primary_only and (aln.is_secondary or aln.is_supplementary):
                continue
            if aln.mapping_quality < args.min_mapq:
                continue
            read_id, monomer_idx = parse_read_id(aln.query_name)
            alns_by_read[read_id].append((aln, monomer_idx))

    # 3. Order fragments within each read
    for read_id in alns_by_read:
        alns = alns_by_read[read_id]
        if alns[0][1] is not None:
            # Has monomer_idx from digest: order by it
            alns.sort(key=lambda x: x[1])
        else:
            # Raw reads: order by query start position (position along read)
            alns.sort(key=lambda x: x[0].query_alignment_start)

    # 4. Assign fragment IDs and write annotated BAM
    with pysam.AlignmentFile(args.input, "rb", threads=args.threads) as bam_in:
        header = bam_in.header.copy()
        with tempfile.NamedTemporaryFile(suffix=".bam", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with pysam.AlignmentFile(tmp_path, "wb", header=header, threads=args.threads) as bam_out:
                for read_id in sorted(alns_by_read.keys()):
                    alns = alns_by_read[read_id]
                    for frag_idx, (aln, _) in enumerate(alns):
                        # Assign fragment ID: chr:start-end (genomic coords)
                        ref_id = aln.reference_id
                        ref_name = bam_in.get_reference_name(ref_id) if ref_id >= 0 else "."
                        ref_start = aln.reference_start + 1  # 1-based
                        ref_end = aln.reference_end
                        frag_id = f"{ref_name}:{ref_start}-{ref_end}"

                        # Add tags: FI (fragment index), FD (fragment id)
                        aln = aln.copy()
                        aln.set_tag("FI", frag_idx, "i")
                        aln.set_tag("FD", frag_id, "Z")
                        aln.set_tag("BX", read_id, "Z")  # barcode/read id for grouping

                        bam_out.write(aln)

            # Sort and index output
            pysam.sort("-o", args.output, tmp_path, "-@", str(args.threads))
            pysam.index(args.output, "-@", str(args.threads))
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    main()
