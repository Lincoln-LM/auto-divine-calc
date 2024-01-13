"""Divine conditions to be checked during seed testing"""


from typing import NamedTuple

import numba
import numpy as np

from . import java_random


class GenericCondition(NamedTuple):
    """Generic rng condition to be checked"""

    salt: np.int64
    int_maximum: np.int64
    int_value: np.int64
    float_maximum: np.float64


def build_buried_treasure_condition(chunk_x: int, chunk_z: int) -> GenericCondition:
    """Build a GenericCondition checking if a buried treasure can spawn at the provided chunk"""
    return GenericCondition(
        np.int64(chunk_x) * np.int64(341873128712)
        + np.int64(chunk_z) * np.int64(132897987541)
        + np.int64(10387320),
        0,
        0,
        0.01,
    )


def build_first_portal_condition(direction: int) -> GenericCondition:
    """
    Build a GenericCondition checking if the direction of the first portal
    of the dimension attempts to spawn in the specified direction
    """
    return GenericCondition(0, 4, direction, 0.0)


def build_third_portal_condition(direction: int) -> GenericCondition:
    """
    Build a GenericCondition checking if the direction of the third portal
    of the dimension attempts to spawn in the specified direction
    """
    # this is hacky, third portal doesn't actually use the float rand
    # but it consumes the same amount of calls
    return GenericCondition(0, 4, direction, 2.0)


numba_GenericCondition = numba.typeof(GenericCondition(0, 0, 0, 0.0))


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
    seed, chance_rand = java_random.next_float(java_random.init(seed + salt))
    if maximum < 0.0:
        chance_rand = -chance_rand
    return chance_rand < maximum


@njit_condition(numba.int64, numba.float32, numba.int64, numba.int64)
def test_float_int_pair_rand(seed, salt, float_maximum, int_maximum, int_value):
    """
    Test if the first random float [0, 1.0)
    of a generator with the provided salt results in a value under the provided maximum
    *and* the second random int [0, int_maximum) results in the provided value
    """
    seed, chance_rand = java_random.next_float(java_random.init(seed + salt))
    if float_maximum < 0.0:
        chance_rand = -chance_rand
    if chance_rand > float_maximum:
        return False
    seed = java_random.next_seed(seed)
    return java_random.next_int(seed, int_maximum)[1] == int_value


@njit_condition(numba.types.ListType(numba_GenericCondition))
def test_all_conditions(seed, conditions):
    """Test a list of GenericConditions sequentially"""
    for condition in conditions:
        if condition[1] != 0:
            if condition[3] != 0.0:
                if not test_float_int_pair_rand(
                    seed, condition[0], condition[3], condition[1], condition[2]
                ):
                    return False
            else:
                if not test_int_rand(seed, condition[0], condition[1], condition[2]):
                    return False
        else:
            if not test_float_rand(seed, condition[0], condition[3]):
                return False
    return True


@njit_condition(numba.types.ListType(numba.types.Tuple((numba.int64, numba.float32))))
def test_floats(seed, pairs):
    """Test a list of (salt, maximum) pairs sequentially"""
    for salt, maximum in pairs:
        if not test_float_rand(seed, salt, maximum):
            return False
    return True


@njit_condition(
    numba.types.ListType(numba.types.Tuple((numba.int64, numba.int64, numba.int64)))
)
def test_ints(seed, pairs):
    """Test a list of (salt, maximum, value) pairs sequentially"""
    for salt, maximum, value in pairs:
        if not test_int_rand(seed, salt, maximum, value):
            return False
    return True
