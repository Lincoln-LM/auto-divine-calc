"""Divine conditions to be checked during seed testing"""


from typing import NamedTuple

import numba
import numpy as np

from . import java_random


class GenericCondition(NamedTuple):
    """Generic rng condition to be checked"""

    int_maximum: np.int64 = np.int64(0)
    int_value: np.int64 = np.int64(0)
    float_minimum: np.float64 = np.float64(0.0)
    float_maximum: np.float64 = np.float64(0.0)


class GenericConditionSet(NamedTuple):
    """Generic set of rng conditions to be checked"""

    salt: np.int64 = np.int64(0)
    condition_0: GenericCondition = GenericCondition()
    condition_1: GenericCondition = GenericCondition()
    condition_2: GenericCondition = GenericCondition()
    condition_3: GenericCondition = GenericCondition()


numba_GenericConditionSet = numba.typeof(GenericConditionSet())


@numba.njit(numba.boolean(numba.int64, numba_GenericConditionSet))
def test_condition_set(seed: np.int64, condition_set: GenericConditionSet) -> bool:
    """Test if a seed passes a set of conditions"""
    seed = java_random.init(seed + condition_set.salt)

    if condition_set.condition_0.int_maximum != 0:
        seed, int_rand = java_random.next_int(
            seed, condition_set.condition_0.int_maximum
        )
        if int_rand != condition_set.condition_0.int_value:
            return False
    elif condition_set.condition_0.float_maximum != 0.0:
        seed, float_rand = java_random.next_float(seed)
        if not (
            condition_set.condition_0.float_minimum
            <= float_rand
            <= condition_set.condition_0.float_maximum
        ):
            return False
    else:
        seed = java_random.next_seed(seed)

    if condition_set.condition_1.int_maximum != 0:
        seed, int_rand = java_random.next_int(
            seed, condition_set.condition_1.int_maximum
        )
        if int_rand != condition_set.condition_1.int_value:
            return False
    elif condition_set.condition_1.float_maximum != 0.0:
        seed, float_rand = java_random.next_float(seed)
        if not (
            condition_set.condition_1.float_minimum
            <= float_rand
            <= condition_set.condition_1.float_maximum
        ):
            return False
    else:
        seed = java_random.next_seed(seed)

    if condition_set.condition_2.int_maximum != 0:
        seed, int_rand = java_random.next_int(
            seed, condition_set.condition_2.int_maximum
        )
        if int_rand != condition_set.condition_2.int_value:
            return False
    elif condition_set.condition_2.float_maximum != 0.0:
        seed, float_rand = java_random.next_float(seed)
        if not (
            condition_set.condition_2.float_minimum
            <= float_rand
            <= condition_set.condition_2.float_maximum
        ):
            return False
    else:
        seed = java_random.next_seed(seed)

    if condition_set.condition_3.int_maximum != 0:
        seed, int_rand = java_random.next_int(
            seed, condition_set.condition_3.int_maximum
        )
        if int_rand != condition_set.condition_3.int_value:
            return False
    elif condition_set.condition_3.float_maximum != 0.0:
        seed, float_rand = java_random.next_float(seed)
        if not (
            condition_set.condition_3.float_minimum
            <= float_rand
            <= condition_set.condition_3.float_maximum
        ):
            return False
    else:
        seed = java_random.next_seed(seed)

    return True


@numba.njit(numba.boolean(numba.int64, numba.types.ListType(numba_GenericConditionSet)))
def test_all_conditions(seed, conditions):
    """Test a list of GenericConditionSets sequentially"""
    for condition in conditions:
        if not test_condition_set(seed, condition):
            return False
    return True


def build_buried_treasure_condition(chunk_x: int, chunk_z: int) -> GenericConditionSet:
    """Build a GenericConditionSet checking if a buried treasure can spawn at the provided chunk"""
    return GenericConditionSet(
        np.int64(chunk_x) * np.int64(341873128712)
        + np.int64(chunk_z) * np.int64(132897987541)
        + np.int64(10387320),
        condition_0=GenericCondition(float_maximum=np.float64(0.01)),
    )


def build_first_portal_condition(direction: int) -> GenericConditionSet:
    """
    Build a GenericConditionSet checking if the direction of the first portal
    of the dimension attempts to spawn in the specified direction
    """
    return GenericConditionSet(
        condition_0=GenericCondition(
            int_maximum=np.int64(4), int_value=np.int64(direction)
        )
    )


def build_second_portal_condition(direction: int) -> GenericConditionSet:
    """
    Build a GenericConditionSet checking if the direction of the second portal
    of the dimension attempts to spawn in the specified direction
    """
    return GenericConditionSet(
        condition_1=GenericCondition(
            int_maximum=np.int64(4), int_value=np.int64(direction)
        )
    )


def build_third_portal_condition(direction: int) -> GenericConditionSet:
    """
    Build a GenericConditionSet checking if the direction of the third portal
    of the dimension attempts to spawn in the specified direction
    """
    return GenericConditionSet(
        condition_2=GenericCondition(
            int_maximum=np.int64(4), int_value=np.int64(direction)
        )
    )
