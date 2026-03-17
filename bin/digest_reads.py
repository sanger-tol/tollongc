#!/usr/bin/env python3
"""
Copyright (c) 2024,2025 Genome Research Ltd.
@author: Yumi Sims, yy5@sanger.ac.uk
Digest Pore-C/Long-C concatemer reads into monomers using seqkit.

Uses seqkit for I/O and splits sequences at restriction enzyme recognition sites.
Requires seqkit to be in PATH.

Usage:
    digest_reads.py --input <fastq> --output <fastq.gz> --cutter <enzyme>

Example:
    digest_reads.py --input reads.fastq.gz --output digested.fastq.gz --cutter NlaIII
"""
from __future__ import annotations

import argparse
import re
import subprocess
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
    # Try exact match first
    if cutter in ENZYME_SITES:
        return ENZYME_SITES[cutter]
    # Try case-insensitive
    for name, site in ENZYME_SITES.items():
        if name.lower() == cutter.lower():
            return site
    # Assume cutter is the recognition sequence itself
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
    # remainder after last cut
    if last_end < len(seq):
        frag_seq = seq[last_end:]
        frag_qual = qual[last_end:] if qual else ""
        if len(frag_seq) >= min_len:
            monomers.append((frag_seq, frag_qual))
    return monomers


def main():
    parser = argparse.ArgumentParser(description="Digest concatemer reads into monomers using seqkit")
    parser.add_argument("--input", required=True, help="Input FASTQ file (plain or gzipped)")
    parser.add_argument("--output", required=True, help="Output FASTQ.gz file")
    parser.add_argument("--cutter", default="NlaIII", help="Restriction enzyme (e.g. NlaIII, DpnII) or recognition sequence")
    parser.add_argument("--min-len", type=int, default=10, help="Minimum monomer length (default: 10)")
    args = parser.parse_args()

    site = get_site(args.cutter)

    # Run seqkit fx2tab -> digest -> seqkit tab2fx (streaming)
    proc1 = subprocess.Popen(
        ["seqkit", "fx2tab", "-n", "-i", "-q", args.input],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    proc2 = subprocess.Popen(
        ["seqkit", "tab2fx", "-o", args.output],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        for line in proc1.stdout:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            name = parts[0]
            seq = parts[1]
            qual = parts[2] if len(parts) > 2 else ""

            monomers = split_at_site(seq, qual, site, args.min_len)
            for i, (m_seq, m_qual) in enumerate(monomers):
                proc2.stdin.write(f"{name}:{i}\t{m_seq}\t{m_qual}\n")
    finally:
        proc2.stdin.close()

    proc1.wait()
    proc2.wait()

    if proc1.returncode != 0:
        sys.stderr.write(proc1.stderr.read() if proc1.stderr else "")
        sys.exit(proc1.returncode)
    if proc2.returncode != 0:
        sys.stderr.write(proc2.stderr.read() if proc2.stderr else "")
        sys.exit(proc2.returncode)


if __name__ == "__main__":
    main()
