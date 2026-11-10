"""Near-duplicate grouping by pHash Hamming distance (union-find).

Moved from scripts/build_unified_dataset.py. Phase 1 called it once per
(source, label); Stage 1 calls it once over ALL images (Decision 15).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np


def hamming_matrix_row(h: np.ndarray, i: int) -> np.ndarray:
    """Hamming distances from h[i] to h[i+1:] (h is uint64)."""
    return np.bitwise_count(np.bitwise_xor(h[i + 1:], h[i]))


def near_dup_groups(hashes: Sequence[int], max_hamming: int) -> list[int]:
    """Group id (a member index) per hash; pairs within max_hamming bits
    are joined transitively."""
    n = len(hashes)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    h = np.array(hashes, dtype=np.uint64)
    for i in range(n):
        dist = hamming_matrix_row(h, i)
        for j in np.nonzero(dist <= max_hamming)[0]:
            a, b = find(i), find(i + 1 + int(j))
            if a != b:
                parent[b] = a
    return [find(i) for i in range(n)]
