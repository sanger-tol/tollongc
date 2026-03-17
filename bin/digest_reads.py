#!/usr/bin/env python3
"""
Copyright (c) 2024,2025 Genome Research Ltd.
@author: Yumi Sims, yy5@sanger.ac.uk
Digest concatemer reads into monomers at restriction enzyme recognition sites.

Reads tabular input (name, seq, qual) from stdin, outputs tabular to stdout.
Designed to be used in a pipeline with seqkit:

  seqkit fx2tab -n -i -q input.fq.gz | digest_reads.py --cutter NlaIII | seqkit tab2fx -o output.fq.gz

Usage:
    digest_reads.py --cutter <enzyme> [--min-len N] < tabular_input > tabular_output

Example:
    seqkit fx2tab -n -i -q reads.fq.gz | digest_reads.py --cutter NlaIII | seqkit tab2fx -o digested.fq.gz
"""
from __future__ import annotations

import argparse
import re
import sys

# Restriction enzyme recognition sequences (case-insensitive)
ENZYME_SITES = {
    "NlaIII": "CATG",
    "DpnII": "GATC",
    "HindIII": "AAGCTT",
    "MboI": "GATC",
    "Sau3AI": "GATC",
}


def get_site(cutter: str) -> str:
    """Get recognition sequence for enzyme name."""
    if cutter in ENZYME_SITES:
        return ENZYME_SITES[cutter]
    for name, site in ENZYME_SITES.items():
        if name.lower() == cutter.lower():
            return site
    if re.match(r"^[ACGTacgt]+$", cutter):
        return cutter.upper()
    raise ValueError(f"Unknown enzyme '{cutter}'. Use one of {list(ENZYME_SITES.keys())} or a recognition sequence (e.g. CATG)")


def split_at_site(seq: str, qual: str, site: str, min_len: int) -> list[tuple[str, str]]:
    """Split sequence and quality at restriction site, return list of (seq, qual) monomers."""
    pattern = re.compile(re.escape(site), re.IGNORECASE)
    monomers = []
    last_end = 0
    for m in pattern.finditer(seq):
        start, end = m.span()
        frag_seq = seq[last_end:start]  # fragment between cuts (exclude site)
        frag_qual = qual[last_end:start] if qual else ""
        if len(frag_seq) >= min_len:
            monomers.append((frag_seq, frag_qual))
        last_end = end
    if last_end < len(seq):
        frag_seq = seq[last_end:]
        frag_qual = qual[last_end:] if qual else ""
        if len(frag_seq) >= min_len:
            monomers.append((frag_seq, frag_qual))
    return monomers


def main():
    parser = argparse.ArgumentParser(
        description="Digest concatemers at restriction sites. Reads tabular (name,seq,qual) from stdin, writes to stdout."
    )
    parser.add_argument("--cutter", default="NlaIII", help="Restriction enzyme (e.g. NlaIII, DpnII) or recognition sequence")
    parser.add_argument("--min-len", type=int, default=10, help="Minimum monomer length (default: 10)")
    args = parser.parse_args()

    site = get_site(args.cutter)

    for line in sys.stdin:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        name = parts[0]
        seq = parts[1]
        qual = parts[2] if len(parts) > 2 else ""

        monomers = split_at_site(seq, qual, site, args.min_len)
        for i, (m_seq, m_qual) in enumerate(monomers):
            sys.stdout.write(f"{name}:{i}\t{m_seq}\t{m_qual}\n")


if __name__ == "__main__":
    main()
