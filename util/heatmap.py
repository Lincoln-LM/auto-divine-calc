import numba
import numpy as np
from numba_progress.numba_atomic import atomic_add

from . import conditions, stronghold


@numba.njit(
    numba.types.types.UniTuple(numba.uint64[:, :], 2)(
        numba.uint64[:],
        numba.uint64,
        numba.uint64,
        numba.types.ListType(conditions.numba_GenericCondition),
    ),
    nogil=True,
    parallel=True,
)
def generate_data(progress, count, thread_count, divine_conditions):
    first_stronghold_locations = np.zeros(701 * 701, dtype=np.uint64)
    all_stronghold_locations = np.zeros(701 * 701, dtype=np.uint64)
    for _ in numba.prange(thread_count):
        while atomic_add(progress, 0, 0) < count:
            seed = np.random.randint(-(1 << 47) + 1, 1 << 47)
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


def convolve_data(data, kernel_size):
    """Convolve 2d map of data by kernel of specified size"""
    kernel = np.fft.fft2(
        np.fft.ifftshift(
            np.pad(
                np.ones((kernel_size, kernel_size)),
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
