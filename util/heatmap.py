import numba
import numpy as np
from numba_progress.numba_atomic import atomic_add

from . import conditions, stronghold


@numba.njit(
    numba.types.types.UniTuple(numba.uint64[:, :], 2)(
        numba.int64[:],
        numba.uint64,
        numba.uint64,
        numba.types.ListType(conditions.numba_GenericCondition),
        numba.int64[:],
    ),
    nogil=True,
    parallel=True,
)
def generate_data(progress, count, thread_count, divine_conditions, seed_list):
    first_stronghold_locations = np.zeros(701 * 701, dtype=np.uint64)
    all_stronghold_locations = np.zeros(701 * 701, dtype=np.uint64)
    chunk_size = count // thread_count
    for thread_number in numba.prange(thread_count):
        start = chunk_size * thread_number
        end = chunk_size * (thread_number + 1)
        if thread_number == thread_count - 1:
            end = count
        for i in range(start, end):
            seed = seed_list[i]
            strongholds = stronghold.gen_first_ring_strongholds(seed)
            if not conditions.test_all_conditions(seed, divine_conditions):
                continue

            atomic_add(
                first_stronghold_locations,
                (strongholds[0][0] * 2 + 350) + 701 * (strongholds[0][1] * 2 + 350),
                1,
            )
            atomic_add(
                all_stronghold_locations,
                (strongholds[0][0] * 2 + 350) + 701 * (strongholds[0][1] * 2 + 350),
                1,
            )
            atomic_add(
                all_stronghold_locations,
                (strongholds[1][0] * 2 + 350) + 701 * (strongholds[1][1] * 2 + 350),
                1,
            )
            atomic_add(
                all_stronghold_locations,
                (strongholds[2][0] * 2 + 350) + 701 * (strongholds[2][1] * 2 + 350),
                1,
            )

            atomic_add(progress, 0, 1)
    return np.reshape(first_stronghold_locations, (701, 701)), np.reshape(
        all_stronghold_locations, (701, 701)
    )


def circular_kernel(kernel_size):
    """Build a circular kernel of the given radius"""

    radius = kernel_size // 2

    def within_radius(x, y):
        return ((x - radius) ** 2 + (y - radius) ** 2 <= radius**2).astype(np.float64)

    return np.fromfunction(within_radius, (kernel_size, kernel_size), dtype=np.float64)


def convolve_data(data, radius):
    """Convolve 2d map of data by circular kernel of specified radius"""
    kernel_size = np.round(radius * 2)
    kernel = np.fft.fft2(
        np.fft.ifftshift(
            np.pad(
                circular_kernel(kernel_size),
                (
                    (((701 - kernel_size) + 1) // 2, (701 - kernel_size) // 2),
                    (((701 - kernel_size) + 1) // 2, (701 - kernel_size) // 2),
                ),
                "constant",
            )
        ),
        s=(701, 701),
    )

    return np.real(np.fft.ifft2(np.fft.fft2(data) * kernel))
