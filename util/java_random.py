"""Functions simulating Java's Random class"""


import numba
import numpy as np

MULT = np.int64(0x5DEECE66D)
ADD = np.int64(0xB)
MASK = np.int64(0xFFFFFFFFFFFF)


@numba.njit(numba.int64(numba.int64))
def init(seed):
    """Salt seed that would be passed to Random()"""
    return np.int64(seed) ^ MULT


@numba.njit(numba.int64(numba.int64))
def next_seed(seed):
    """Advance seed via Java's Random() LCG algorithm"""
    return (np.int64(seed) * MULT + ADD) & MASK


@numba.njit(numba.types.UniTuple(numba.int64, 2)(numba.int64, numba.int64))
def next_int(seed, maximum):
    """Advance seed and generate next int in range [0, maximum)"""
    seed = next_seed(seed)
    maximum = np.uint64(maximum)
    if maximum & (maximum - 1):
        return seed, (seed >> np.uint64(17)) % maximum
    return seed, (maximum * (seed >> np.uint64(17))) >> np.uint64(31)


@numba.njit(numba.types.Tuple((numba.int64, numba.float32))(numba.int64))
def next_float(seed):
    """Advance seed and generate next float32"""
    seed = next_seed(seed)
    return seed, (seed >> np.int64(24)) / np.float32(1 << 24)


@numba.njit(numba.types.Tuple((numba.int64, numba.float64))(numba.int64))
def next_double(seed):
    """Advance seed and generate next float64"""
    seed = np.int64(seed)
    seed = next_seed(seed)
    rand_0 = (seed >> np.int64(22)) << np.int64(27)
    seed = next_seed(seed)
    rand_1 = seed >> np.int64(21)
    return seed, (rand_0 + rand_1) / np.float64(1 << 53)
