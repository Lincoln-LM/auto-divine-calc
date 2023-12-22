"""
Main file to be executed
divine calculations *heavily* based on https://github.com/mjtb49/DivineHeatmapGenerator/
"""

from enum import IntEnum

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib
import numba
import numpy as np
import pyperclip
from numba_progress.numba_atomic import atomic_add


THREADS = numba.get_num_threads()
RESULT_COUNT = 10000
KERNEL_SIZE = 30

matplotlib.use("TkAgg")


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
def next_int(seed, maximum):
    """Advance seed and generate next int in range [0, maximum)"""
    seed = next_seed(seed)
    maximum = np.uint64(maximum)
    if maximum & (maximum - 1):
        return seed, (seed >> np.uint64(17)) % maximum
    return seed, (maximum * (seed >> np.uint64(17))) >> np.uint64(31)


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
def test_decorator_80000_x(seed, x):
    """Test if the decorator with salt near 80000 in chunk 0,0 starts at this X coordinate"""
    seed = next_seed(init(seed + np.int64(80004)))
    x = np.int64(x)
    return (x << np.int64(44)) <= seed < ((x + np.int64(1)) << np.int64(44))


@numba.njit
def test_chance_decorator_80000(seed, z):
    """
    Test if the 0.1 probability decorator with salt near 80000
    in chunk 0,0 starts at this Z coordinate"""
    # TODO: handle 0.05 probability
    seed = init(seed + np.int64(80000))
    seed, chance_rand = next_float(seed)
    if chance_rand > np.float32(0.1):
        return False
    # TODO: x?
    seed = next_seed(seed)
    seed = next_seed(seed)
    z = np.int64(z)
    return (z << np.int64(44)) <= seed < ((z + np.int64(1)) << np.int64(44))


@numba.njit
def test_water(seed):
    """Test if 0,0 can contain a water pool"""
    seed = init(seed + np.int64(10000))
    seed, chance_rand = next_float(seed)
    return chance_rand < np.float32(0.25)


@numba.njit
def test_lava(seed):
    """Test if 0,0 can contain a lava pool"""
    seed = init(seed + np.int64(10000))
    seed, chance_rand = next_float(seed)
    return chance_rand < np.float32(0.125)


@numba.njit
def test_disk_60000_x(seed, x):
    """Test if the disk with salt near 60000 in chunk 0,0 starts at this X coordinate"""
    seed = next_seed(init(seed + np.int64(60012)))
    x = np.int64(x)
    return (x << np.int64(44)) <= seed < ((x + np.int64(1)) << np.int64(44))


@numba.njit
def test_nether_fossil(seed, x):
    """Test if nether fossil in chunk 0,0 starts at this X coordinate"""
    seed = next_seed(init(seed))
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


@numba.njit
def get_first_three_starts_no_biomes(seed):
    """Generate the first 3 stronghold start chunks w/o accounting for biomes"""
    seed = init(seed)
    seed, rand_0 = next_double(seed)
    seed, rand_1 = next_double(seed)
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
    return chunk_x_0, chunk_z_0, chunk_x_1, chunk_z_1, chunk_x_2, chunk_z_2


# technically not foolproof
BT_NULL = -100000
NULL = -1


@numba.njit(nogil=True)
def generate_data(
    count,
    bt_x,
    bt_z,
    portal_orientation,
    decorator_80000_x,
    disk_60000_x,
    nether_fossil_x,
    tundra_tree_z,
    water,
    lava,
):
    """Generate at least ``count`` first stronghold start locations
    based on random seeds that match the buried treasure
    and/or first portal orientation"""

    count = np.int64(count)
    bt_x = np.int64(bt_x)
    bt_z = np.int64(bt_z)
    portal_orientation = np.int64(portal_orientation)
    decorator_80000_x = np.int64(decorator_80000_x)
    disk_60000_x = np.int64(disk_60000_x)
    nether_fossil_x = np.int64(nether_fossil_x)
    tundra_tree_z = np.int64(tundra_tree_z)
    distribution = np.zeros(701 * 701, dtype=np.int64)
    i = np.zeros(1, np.int64)
    for _ in numba.prange(THREADS):
        while i < count:
            seed = np.random.randint(-(1 << 47) + 1, 1 << 47)
            if (
                bt_x != np.int64(BT_NULL)
                and bt_z != np.int64(BT_NULL)
                and not test_bt(seed, bt_x, bt_z)
            ):
                continue
            if portal_orientation != np.int64(NULL) and not test_portal(
                seed, portal_orientation
            ):
                continue
            if decorator_80000_x != np.int64(NULL) and not test_decorator_80000_x(
                seed, decorator_80000_x
            ):
                continue
            if disk_60000_x != np.int64(NULL) and not test_disk_60000_x(
                seed, disk_60000_x
            ):
                continue
            if nether_fossil_x != np.int64(NULL) and not test_nether_fossil(
                seed, nether_fossil_x
            ):
                continue
            if tundra_tree_z != np.int64(NULL) and not test_chance_decorator_80000(
                seed, tundra_tree_z
            ):
                continue
            if water and not test_water(seed):
                continue
            if lava and not test_lava(seed):
                continue
            x_0, z_0, x_1, z_1, x_2, z_2 = get_first_three_starts_no_biomes(seed)
            atomic_add(distribution, ((x_0 * 2) + 350) + ((z_0 * 2) + 350) * 701, 1)
            atomic_add(distribution, ((x_1 * 2) + 350) + ((z_1 * 2) + 350) * 701, 1)
            atomic_add(distribution, ((x_2 * 2) + 350) + ((z_2 * 2) + 350) * 701, 1)
            atomic_add(i, 0, 1)
    return distribution


if __name__ == "__main__":
    bt_x, bt_z = BT_NULL, BT_NULL
    portal_orientation = (
        decorator_80000_x
    ) = disk_60000_x = nether_fossil_x = tundra_tree_z = NULL
    water = lava = False
    last_clipboard = pyperclip.paste()
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
    # TODO: configuration option
    canvas = plt.figure().canvas
    canvas.manager.window.attributes("-topmost", 1)

    scanning = None

    def key_press_event(event) -> None:
        """Handle key press events on the figure window"""
        global bt_x, bt_z, portal_orientation, nether_fossil_x, decorator_80000_x, disk_60000_x, tundra_tree_z, water, lava, scanning
        # TODO: configuration option
        if event.key == "r":
            bt_x = bt_z = BT_NULL
            portal_orientation = (
                nether_fossil_x
            ) = decorator_80000_x = disk_60000_x = tundra_tree_z = NULL
            water = lava = False
            plt.clf()
        elif event.key == "w":
            water = True
            scanning = False
        elif event.key == "l":
            lava = True
            scanning = False

    canvas.mpl_connect("key_press_event", key_press_event)
    while True:
        scanning = True
        while scanning:
            # update every 5 checks
            for _ in range(5):
                clipboard = pyperclip.paste()
                if clipboard != last_clipboard and "minecraft" in clipboard:
                    scanning = False
                    break
            plt.draw()
            plt.gcf().canvas.draw_idle()
            plt.gcf().canvas.start_event_loop(0.001)
        last_clipboard = clipboard
        # f3+i
        if "setblock" in last_clipboard:
            _, x, y, z, full_block = last_clipboard.split(" ")
            x, y, z = int(x), int(y), int(z)
            block_name, *_ = full_block.split("[")
            if block_name == "minecraft:chest":
                bt_x, bt_z = x >> 4, z >> 4
                print(f"{block_name=} {bt_x=} {bt_z=}")
            elif 0 <= x <= 15 and 0 <= z <= 15:
                if "log" in block_name:
                    tundra_tree_z = z
                    print(f"{block_name=} {tundra_tree_z=}")
                elif block_name == "minecraft:bone_block":
                    nether_fossil_x = x
                    print(f"{block_name=} {nether_fossil_x=}")
                elif block_name in (
                    "minecraft:clay",
                    "minecraft:gravel",
                    "minecraft:sand",
                ):
                    disk_60000_x = x
                    print(f"{block_name=} {disk_60000_x=}")
                else:
                    decorator_80000_x = x
                    print(f"{block_name=} {decorator_80000_x=}")
        # first f3+c in the nether
        elif (
            "execute in minecraft:the_nether" in last_clipboard
            and portal_orientation == NULL
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
        if (
            BT_NULL not in (bt_x, bt_z)
            or not all(
                x == NULL
                for x in (
                    portal_orientation,
                    nether_fossil_x,
                    decorator_80000_x,
                    disk_60000_x,
                    tundra_tree_z,
                )
            )
            or True in (water, lava)
        ):
            print("Generating ....")
            raw_data = np.reshape(
                generate_data(
                    RESULT_COUNT,
                    bt_x,
                    bt_z,
                    portal_orientation,
                    decorator_80000_x,
                    disk_60000_x,
                    nether_fossil_x,
                    tundra_tree_z,
                    water,
                    lava,
                ),
                (701, 701),
            )
            print("Generated.")

            convoled_data = np.real(
                np.fft.ifft2(
                    np.fft.fft2(raw_data) * np.fft.fft2(KERNEL, s=raw_data.shape)
                )
            )
            plt.clf()
            plt.imshow(
                convoled_data,
                origin="upper",
                cmap="hot",
                interpolation="nearest",
                extent=[-350, 350, 350, -350],
            )
            coords = divmod(np.argmax(convoled_data), 701)
            coords = coords[1] - 350, coords[0] - 350
            for ofs in range(3):
                pt = (
                    coords[0] * np.cos(ofs * (2 / 3 * np.pi))
                    - coords[1] * np.sin(ofs * (2 / 3 * np.pi)),
                    coords[1] * np.cos(ofs * (2 / 3 * np.pi))
                    + coords[0] * np.sin(ofs * (2 / 3 * np.pi)),
                )
                plt.plot(
                    *pt,
                    marker="*",
                    c="green",
                )
                plt.text(
                    *pt,
                    f"{round(pt[0])} {round(pt[1])}",
                    size=12,
                    color="black",
                    path_effects=[pe.withStroke(linewidth=4, foreground="green")],
                )
        # update window w/o stealing focus
        plt.draw()
        plt.gcf().canvas.draw_idle()
        plt.gcf().canvas.start_event_loop(0.001)
