"""Divine conditions to be checked during seed testing"""


import numba
import numpy as np

from . import java_random


def njit_condition(*args, **kwargs):
    """JIT-compiled condition function taking in a seed and returning success or failure"""
    return numba.njit(numba.boolean(numba.int64, *args), **kwargs)


@njit_condition(numba.int64, numba.int64, numba.int64)
def test_int_rand(seed, salt, maximum, value):
    """
    Test if the first random integer [0, maximum)
    of a generator with the provided salt results in the provided value
    """
    return value == java_random.next_int(java_random.init(seed + salt), maximum)[1]


@njit_condition(numba.int64, numba.float32)
def test_float_rand(seed, salt, maximum):
    """
    Test if the first random float [0, 1.0)
    of a generator with the provided salt results in a value under the provided maximum
    """
    return java_random.next_float(java_random.init(seed + salt))[1] < maximum


@njit_condition(numba.int64, numba.float32, numba.int64, numba.int64):
def test_float_int_pair_rand(seed, salt, float_maximum, int_maximum, int_value):
    """
    Test if the first random float [0, 1.0)
    of a generator with the provided salt results in a value under the provided maximum
    *and* the second random int [0, int_maximum) results in the provided value"""
    seed, chance_rand = java_random.next_float(java_random.init(seed + salt))
    if chance_rand > float_maximum:
        return False
    seed = java_random.next_seed(seed)
    return java_random.next_int(seed, int_maximum) == int_value

@njit_condition(numba.types.List(numba.types.Tuple((numba.int64, numba.float32))))
def test_floats(seed, pairs):
    """Test a list of (salt, maximum) pairs sequentially"""
    for salt, maximum in pairs:
        if not test_float_rand(seed, salt, maximum):
            return False
    return True


@njit_condition(
    numba.types.List(numba.types.Tuple((numba.int64, numba.int64, numba.int64)))
)
def test_ints(seed, pairs):
    """Test a list of (salt, maximum, value) pairs sequentially"""
    for salt, maximum, value in pairs:
        if not test_int_rand(seed, salt, maximum, value):
            return False
    return True
