"""
Main file to be executed
divine calculations *heavily* based on https://github.com/mjtb49/DivineHeatmapGenerator/
"""

from enum import IntEnum

import matplotlib.pyplot as plt
import numba
import numpy as np
import pyperclip
from numba_progress.numba_atomic import atomic_add


THREADS = numba.get_num_threads()
RESULT_COUNT = 10000
KERNEL_SIZE = 16


class PortalOrientation(IntEnum):
    """Cardinal directions as divine-relevant value"""

    EAST = 0
    NORTH = 1
    WEST = 2
    SOUTH = 3


@numba.njit
def next_seed(seed):
    """Advance seed via Java's Random() LCG algorithm"""
    return (np.int64(seed) * np.int64(0x5DEECE66D) + np.int64(11)) & np.int64(
        0xFFFFFFFFFFFF
    )


@numba.njit
def next_float(seed):
    """Advance seed and generate next float32"""
    seed = next_seed(seed)
    return seed, (seed >> np.int64(24)) / np.float32(0x1000000)


@numba.njit
def next_double(seed):
    """Advance seed and generate next float64"""
    seed = np.int64(seed)
    seed = next_seed(seed)
    rand_0 = (seed >> np.int64(22)) << np.int64(27)
    seed = next_seed(seed)
    rand_1 = seed >> np.int64(21)
    return seed, (rand_0 + rand_1) / np.float64(0x20000000000000)


@numba.njit
def init(seed):
    """Salt seed that would be passed to Random()"""
    return np.int64(seed) ^ np.int64(0x5DEECE66D)


@numba.njit
def test_bt(seed, chunk_x, chunk_z):
    """Test if a buried treasure would be generated in this chunk on this seed"""
    x = np.int64(chunk_x)
    z = np.int64(chunk_z)
    salt = x * np.int64(341873128712) + z * np.int64(132897987541) + np.int64(10387320)
    seed = np.int64(seed) + salt
    return next_float(init(seed))[1] < np.float64(0.01)


@numba.njit
def test_portal(seed, direction):
    """Test if the first portal's orientation matches the given direction"""
    seed = next_seed(init(seed))
    direction = np.int64(direction)
    return (
        (direction << np.int64(46))
        <= seed
        < ((direction + np.int64(1)) << np.int64(46))
    )


@numba.njit
def test_nether_tree(seed, x):
    """Test if trees in chunk 0,0 in the nether start at this X coordinate"""
    seed = next_seed(init(seed + np.int64(80004)))
    x = np.int64(x)
    return (x << np.int64(44)) <= seed < ((x + np.int64(1)) << np.int64(44))


@numba.njit
def get_first_start_no_biomes(seed):
    """Generate the first stronghold start chunk w/o accounting for biomes"""
    seed = init(seed)
    seed, rand_0 = next_double(seed)
    seed, rand_1 = next_double(seed)
    angle = rand_0 * np.pi * np.float64(2)
    distance_ring = np.double(4) * np.double(32) + (
        rand_1 - np.float64(0.5)
    ) * np.float64(32) * np.float64(2.5)
    chunk_x = np.int64(np.round(np.cos(angle) * distance_ring))
    chunk_z = np.int64(np.round(np.sin(angle) * distance_ring))
    return chunk_x, chunk_z


# technically not foolproof
BT_NULL = -100000
PORTAL_NULL = -1


@numba.njit(nogil=True)
def generate_data(count, bt_x, bt_y, portal_orientation):
    """Generate at least ``count`` first stronghold start locations
    based on random seeds that match the buried treasure
    and/or first portal orientation"""

    count = np.int64(count)
    bt_x = np.int64(bt_x)
    bt_y = np.int64(bt_y)
    portal_orientation = np.int64(portal_orientation)
    distribution = np.zeros(701 * 701, dtype=np.int64)
    i = np.zeros(1, np.int64)
    for _ in numba.prange(THREADS):
        while i < count:
            seed = np.random.randint(-(1 << 47) + 1, 1 << 47)
            if (
                bt_x != np.int64(BT_NULL)
                and bt_y != np.int64(BT_NULL)
                and not test_bt(seed, bt_x, bt_y)
            ):
                continue
            if portal_orientation != np.int64(PORTAL_NULL) and not test_portal(
                seed, portal_orientation
            ):
                continue
            # TODO: nether tree divine
            x, z = get_first_start_no_biomes(seed)
            atomic_add(distribution, ((x * 2) + 350) + ((z * 2) + 350) * 701, 1)
            atomic_add(i, 0, 1)
    return distribution


if __name__ == "__main__":
    bt_x, bt_z = BT_NULL, BT_NULL
    portal_orientation = PORTAL_NULL
    last_clipboard = pyperclip.paste()
    # run once to jit compile
    # TODO: just specify argument types lol
    generate_data(
        RESULT_COUNT,
        -1,
        12,
        0,
    )
    size = 701 - KERNEL_SIZE
    KERNEL = np.fft.ifftshift(
        np.pad(
            np.ones((KERNEL_SIZE, KERNEL_SIZE)),
            (
                ((size + 1) // 2, size // 2),
                ((size + 1) // 2, size // 2),
            ),
            "constant",
        )
    )
    plt.ion()
    while True:
        plt.clf()
        while True:
            clipboard = pyperclip.paste()
            if clipboard != last_clipboard and "minecraft" in clipboard:
                break
        last_clipboard = clipboard
        # first f3+i
        if "setblock" in last_clipboard:
            _, x, y, z, full_block = last_clipboard.split(" ")
            block_name, *_ = full_block.split("[")
            bt_x, bt_z = int(x) >> 4, int(z) >> 4
            print(f"{block_name=} {bt_x=} {bt_z=}")
        # first f3+c in the nether
        elif (
            "execute in minecraft:the_nether" in last_clipboard
            and portal_orientation == PORTAL_NULL
        ):
            _, _, _, _, _, _, _, _, _, yaw, _ = last_clipboard.split(" ")
            yaw = float(yaw) % 360
            yaw = yaw if yaw <= 180.0 else yaw - 360
            if yaw > 135 or yaw < -135:
                portal_orientation = PortalOrientation.NORTH.value
            elif yaw <= -45:
                portal_orientation = PortalOrientation.EAST.value
            elif yaw <= 45:
                portal_orientation = PortalOrientation.SOUTH.value
            elif yaw <= 135:
                portal_orientation = PortalOrientation.WEST.value
            print(f"{yaw=} {portal_orientation=}")
        if BT_NULL not in (bt_x, bt_z) or portal_orientation != PORTAL_NULL:
            raw_data = np.reshape(
                generate_data(
                    RESULT_COUNT,
                    bt_x,
                    bt_z,
                    portal_orientation,
                ),
                (701, 701),
            )

            convoled_data = np.real(
                np.fft.ifft2(
                    np.fft.fft2(raw_data) * np.fft.fft2(KERNEL, s=raw_data.shape)
                )
            )
            plt.imshow(
                convoled_data,
                origin="upper",
                cmap="hot",
                interpolation="nearest",
                extent=[-350, 350, 350, -350],
            )
        # update window w/o stealing focus
        plt.draw()
        plt.gcf().canvas.draw_idle()
        plt.gcf().canvas.start_event_loop(0.1)
