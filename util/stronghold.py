"""Stronghold generation functions"""

import numba
import numpy as np

from . import java_random


@numba.njit(numba.UniTuple(numba.UniTuple(np.int64, 2), 3))
def gen_first_ring_strongholds(seed):
    """Generate the first 3 stronghold start chunks w/o accounting for biomes"""
    seed = java_random.init(seed)
    seed, rand_0 = java_random.next_double(seed)
    seed, rand_1 = java_random.next_double(seed)
    angle = rand_0 * np.pi * np.float64(2)
    distance_ring = np.float64(4) * np.float64(32) + (
        rand_1 - np.float64(0.5)
    ) * np.float64(32) * np.float64(2.5)
    chunk_x_0 = np.int64(np.round(np.cos(angle) * distance_ring))
    chunk_z_0 = np.int64(np.round(np.sin(angle) * distance_ring))
    angle += np.pi * 2.0 / 3.0
    distance_ring = np.float64(4) * np.float64(32) + (
        rand_1 - np.float64(0.5)
    ) * np.float64(32) * np.float64(2.5)
    chunk_x_1 = np.int64(np.round(np.cos(angle) * distance_ring))
    chunk_z_1 = np.int64(np.round(np.sin(angle) * distance_ring))
    angle += np.pi * 2.0 / 3.0
    distance_ring = np.float64(4) * np.float64(32) + (
        rand_1 - np.float64(0.5)
    ) * np.float64(32) * np.float64(2.5)
    chunk_x_2 = np.int64(np.round(np.cos(angle) * distance_ring))
    chunk_z_2 = np.int64(np.round(np.sin(angle) * distance_ring))
    return (chunk_x_0, chunk_z_0), (chunk_x_1, chunk_z_1), (chunk_x_2, chunk_z_2)
