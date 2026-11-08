"""E15: near-duplicate grouping moved to src.common.neardup."""

from src.common.neardup import near_dup_groups


def test_groups_within_hamming():
    hashes = [0b0000, 0b0011, 0b1111_0000_0000, 0b1111_0000_0001]
    gid = near_dup_groups(hashes, max_hamming=2)
    assert gid[0] == gid[1]
    assert gid[2] == gid[3]
    assert gid[0] != gid[2]


def test_transitive_union():
    # 0-1 distance 2, 1-2 distance 2, 0-2 distance 4: one group by transitivity
    hashes = [0b0000, 0b0011, 0b1111]
    gid = near_dup_groups(hashes, max_hamming=2)
    assert len(set(gid)) == 1


def test_threshold_is_respected():
    assert len(set(near_dup_groups([0b0000, 0b0111], max_hamming=2))) == 2
    assert len(set(near_dup_groups([0b0000, 0b0111], max_hamming=3))) == 1
