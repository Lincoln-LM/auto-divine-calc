"""Main CTk GUI to be run"""

import logging
import pickle
from collections import deque, defaultdict
from functools import partial
from threading import Thread
from time import sleep
from tkinter import Menu

import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numba import config as numba_config
from numba.typed import List as TypedList
from pynput import keyboard

from util.clipboard import ClipboardListener
from util.condition_widget import (
    BuriedTreasureDialog,
    ShipwreckDialog,
    ChanceDecoratorDialog,
    ConditionList,
    DecoratorDialog,
    DiskDialog,
    NetherFossilDialog,
)
from util.conditions import (
    GenericCondition,
    build_first_portal_condition,
    build_third_portal_condition,
    numba_GenericCondition,
)
from util.heatmap import convolve_data, generate_data

logging.basicConfig()


def validate_thread_count(value: str) -> bool:
    """Validate if a thread count value is within the valid range"""
    return (
        not value
        or value.isdigit()
        and 1 <= int(value) <= numba_config.NUMBA_DEFAULT_NUM_THREADS
    )


class ProgressThread(Thread):
    """Thread to log progress of stronghold distribution generation"""

    def __init__(self, parent_logger, progress, sample_count):
        super().__init__(daemon=True)
        self.progress = progress
        self.logger = parent_logger.getChild("ProgressThread")
        self.sample_count = sample_count

    def run(self):
        while 0 <= self.progress[0] < self.sample_count:
            self.logger.info(
                "Generated %d/%d samples (%.02f%%)",
                self.progress[0],
                self.sample_count,
                self.progress[0] / self.sample_count * 100,
            )
            sleep(0.05)


class KeybindWindow(ctk.CTkToplevel):
    """Keybind settings window"""

    KEYBINDS = ["Reset", "Toggle Clipboard Listener"]

    def __init__(self, master, config_location):
        super().__init__(master)
        self.grab_set()

        self.title("Keybind Settings")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.config_location = config_location
        self.buttons = []
        self.active_button = None

        # TODO: I kind of hate using pickle for this but keycodes are weird
        try:
            with open(self.config_location, "rb") as config_file:
                self.config = pickle.load(config_file)
        except FileNotFoundError:
            self.config = {}
        self.config.setdefault

        for i, name in enumerate(self.KEYBINDS):
            value = self.config.setdefault("keybinds", {}).get(name, None)
            if value is not None:
                if isinstance(value, str):
                    value = keyboard.KeyCode.from_char(value)
                elif isinstance(value, int):
                    value = keyboard.Key(value)
            ctk.CTkLabel(self, text=f"{name}:").grid(row=i, column=0)
            button = ctk.CTkButton(self, text=" + ".join(map(str, value or (None,))))

            def on_press(name, button):
                if self.active_button == (name, button):
                    button.configure(
                        text=" + ".join(
                            map(
                                str,
                                self.config.setdefault("keybinds", {}).get(
                                    name, (None,)
                                ),
                            )
                        )
                    )
                    self.active_button = None
                else:
                    self.active_button = (name, button)
                    button.configure(text="...")

            button.configure(command=partial(on_press, name, button))
            button.grid(row=i, column=1, padx=3, pady=3)
            self.buttons.append(button)

    def on_close(self):
        """Toplevel close handler"""
        with open(self.config_location, "wb+") as config_file:
            pickle.dump(self.config, config_file)
        # hacky
        self.master.config = self.config
        self.master.keybind_window = None
        self.destroy()

    def set_active_keybind(self, keycombo):
        """Set the value for the currently active keybind"""
        self.config.setdefault("keybinds", {})[self.active_button[0]] = keycombo
        self.active_button[1].configure(text=" + ".join(map(str, keycombo)) + " ...")


class MainApplication(ctk.CTk):
    """Main CTk GUI to be run"""

    CONFIG_LOCATION = "config.pkl"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("MainApplication")
        self.logger.setLevel(logging.INFO)
        ctk.set_appearance_mode("dark")
        self.configure_mpl_theme()

        self.title("Auto Divine Calculator")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.first_sh_distribution = self.all_sh_distribution = None

        self.popout_window = None
        self.keybind_window = None

        try:
            with open(self.CONFIG_LOCATION, "rb") as config_file:
                self.config = pickle.load(config_file)
        except FileNotFoundError:
            self.config = {}

        self.held_keys = defaultdict(lambda: False)
        self.keypress_listener = keyboard.Listener(
            on_press=self.key_press_handler, on_release=self.key_release_handler
        )
        self.clipboard_listener = ClipboardListener(on_change=self.clipboard_handler)

        self.keypress_listener.start()
        self.clipboard_listener.start()

        self.place_widgets()

    def on_close(self):
        """Window close handler"""
        self.config["thread_count"] = int(self.thread_count_entry.get())
        self.config["sample_count"] = int(self.sample_count_entry.get())
        self.config["maximum_distance"] = int(self.maximum_distance_slider.get())
        with open(self.CONFIG_LOCATION, "wb+") as config_file:
            pickle.dump(self.config, config_file)
        self.destroy()

    def configure_mpl_theme(self):
        """Set the default colors of the embedded plots"""
        # TODO: this is ugly
        plt.rcParams["axes.facecolor"] = plt.rcParams["figure.facecolor"] = tuple(
            c / 65535
            for c in self.winfo_rgb(
                ctk.ThemeManager.theme["CTk"]["fg_color"][
                    ctk.AppearanceModeTracker.appearance_mode
                ]
            )
        )
        plt.rcParams["axes.edgecolor"] = plt.rcParams["xtick.color"] = plt.rcParams[
            "ytick.color"
        ] = tuple(
            c / 65535
            for c in self.winfo_rgb(
                ctk.ThemeManager.theme["CTkLabel"]["text_color"][
                    ctk.AppearanceModeTracker.appearance_mode
                ]
            )
        )

    def place_widgets(self):
        """Place CTk widgets on the window"""

        row = 0
        self.thread_count_label = ctk.CTkLabel(self, text="Thread Count:")
        self.thread_count_label.grid(row=row, column=0)
        self.thread_count_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(self.register(validate_thread_count), "%P"),
        )
        self.thread_count_entry.insert(0, str(self.config.get("thread_count", 1)))
        self.thread_count_entry.grid(row=row, column=1)
        self.thread_count_label = ctk.CTkLabel(self, text="Thread Count:")
        self.thread_count_label.grid(row=row, column=0)
        self.divine_condition_list = ConditionList(self, command=self.draw_heatmap)
        self.divine_condition_list.grid(row=row, column=2, rowspan=5)

        self.configure_menubar()

        row += 1
        self.sample_count_label = ctk.CTkLabel(self, text="Sample Count:")
        self.sample_count_label.grid(row=row, column=0)
        self.sample_count_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.sample_count_entry.insert(0, str(self.config.get("sample_count", 100000)))
        self.sample_count_entry.grid(row=row, column=1)

        row += 1
        self.maximum_distance_label = ctk.CTkLabel(self)
        self.maximum_distance_label.grid(row=row, column=0)
        self.maximum_distance_slider = ctk.CTkSlider(
            self, from_=1, to=2000, command=self.maximum_distance_handler, width=400
        )
        self.maximum_distance_slider.grid(row=row, column=1)
        self.maximum_distance_slider.set(self.config.get("maximum_distance", 500))
        self.maximum_distance_handler(self.config.get("maximum_distance", 500))
        self.fig, self.axes = plt.subplots(1, 2)
        self.popout_fig, self.popout_axes = plt.subplots(1, 2)

        row += 1
        self.popout_button = ctk.CTkButton(
            self,
            width=30,
            text="⇱",
            command=self.popout,
        )
        self.popout_button.grid(row=row, column=0)
        self.regenerated_button = ctk.CTkButton(
            self,
            width=300,
            text="Regenerate Stronghold Distribution",
            command=self.draw_heatmap,
        )
        self.regenerated_button.grid(row=row, column=1)

        row += 1
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=row, column=0, columnspan=2)
        self.popout_canvas = None

        row += 1
        self.coords_display = ctk.CTkLabel(self, text="")
        self.coords_display.grid(row=row, column=0, columnspan=2)
        self.popout_coords_display = None

    def popout(self):
        """Pop-out heatmap as its own window"""
        if self.popout_window is not None:
            self.popout_window.destroy()
            self.popout_window = None
        self.popout_window = ctk.CTkToplevel(self)
        self.popout_window.title("Auto Divine Calculator")
        self.popout_window.attributes("-topmost", True)

        def on_close():
            self.popout_coords_display = None
            self.popout_canvas = None
            self.popout_window.destroy()
            self.popout_window = None

        self.popout_window.protocol("WM_DELETE_WINDOW", on_close)
        self.popout_canvas = FigureCanvasTkAgg(self.popout_fig, self.popout_window)
        self.popout_canvas.get_tk_widget().configure(height=100, width=250)
        self.popout_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.popout_coords_display = ctk.CTkLabel(
            self.popout_window,
            text=self.coords_display.cget("text"),
            height=50,
            width=250,
        )
        self.popout_coords_display.pack(fill="both", side="bottom", expand=True)

    def open_keybind_window(self):
        """Open keybind settings window"""
        self.keybind_window = KeybindWindow(self, self.CONFIG_LOCATION)

    def configure_menubar(self):
        """Build and configure the menubar at the top of the window"""

        menubar = Menu(self)

        menubar.add_command(label="Keybinds", command=self.open_keybind_window)

        portal_menu = Menu(self, tearoff=0)
        first_portal_menu = Menu(self, tearoff=0)
        third_portal_menu = Menu(self, tearoff=0)
        for i, direction in enumerate(("East", "North", "West", "South")):
            first_portal_menu.add_command(
                label=direction,
                command=partial(
                    self.divine_condition_list.add_condition,
                    build_first_portal_condition(i),
                    name=f"First Portal {direction}",
                    display_float_rand=False,
                    display_int_rand=False,
                    display_salt=False,
                ),
            )
            third_portal_menu.add_command(
                label=direction,
                command=partial(
                    self.divine_condition_list.add_condition,
                    build_third_portal_condition(i),
                    name=f"Third Portal {direction}",
                    display_float_rand=False,
                    display_int_rand=False,
                    display_salt=False,
                ),
            )

        portal_menu.add_cascade(label="First Portal", menu=first_portal_menu)
        portal_menu.add_cascade(label="Third Portal", menu=third_portal_menu)

        zero_zero_menu = Menu(self, tearoff=0)
        zero_zero_menu.add_command(
            label="Water Pool",
            command=lambda: self.divine_condition_list.add_condition(
                GenericCondition(10000, 0, 0, 0.25)
            ),
        )
        zero_zero_menu.add_command(
            label="Lava Pool",
            command=lambda: self.divine_condition_list.add_condition(
                GenericCondition(10000, 0, 0, 0.125)
            ),
        )
        zero_zero_menu.add_command(
            label="Nether Fossil (X)",
            command=lambda: NetherFossilDialog(self.divine_condition_list),
        )
        zero_zero_menu.add_command(
            label="80k Chance Decorator (Z)",
            command=lambda: ChanceDecoratorDialog(self.divine_condition_list),
        )
        zero_zero_menu.add_command(
            label="80k Decorator (X)",
            command=lambda: DecoratorDialog(self.divine_condition_list),
        )
        zero_zero_menu.add_command(
            label="60k Disk Decorator (X)",
            command=lambda: DiskDialog(self.divine_condition_list),
        )

        menubar.add_cascade(label="Portal Orientation", menu=portal_menu)
        menubar.add_cascade(label="Chunk 0,0", menu=zero_zero_menu)
        menubar.add_command(
            label="Buried Treasure",
            command=lambda: BuriedTreasureDialog(self.divine_condition_list),
        )
        menubar.add_command(
            label="1.15 Shipwreck",
            command=lambda: ShipwreckDialog(self.divine_condition_list),
        )
        self.configure(menu=menubar)

    def draw_heatmap(self, new_data: bool = True):
        """Draw heatmaps for the first ring of strongholds"""
        # called too early
        if not hasattr(self, "axes"):
            return
        if new_data:
            sample_count, thread_count = int(self.sample_count_entry.get()), int(
                self.thread_count_entry.get()
            )
            conditions = TypedList.empty_list(numba_GenericCondition)
            deque(map(conditions.append, self.divine_condition_list.conditions), 0)
            self.logger.info(
                "Generating %d samples on %d threads with %d conditions",
                sample_count,
                thread_count,
                len(conditions),
            )
            progress = np.zeros(1, np.int64)

            ProgressThread(self.logger, progress, sample_count).start()
            (
                first_sh_distribution,
                all_sh_distribution,
            ) = generate_data(
                progress,
                sample_count,
                thread_count,
                conditions,
            )
            self.first_sh_distribution = first_sh_distribution / sample_count
            self.all_sh_distribution = all_sh_distribution / sample_count
            self.logger.info("Finished generation")
        elif self.first_sh_distribution is None:
            return
        maximum_distance = round(self.maximum_distance_slider.get() / 8)
        self.axes[0].clear()
        self.axes[1].clear()
        self.popout_axes[0].clear()
        self.popout_axes[1].clear()
        all_convolved_data = convolve_data(self.all_sh_distribution, maximum_distance)
        first_convolved_data = convolve_data(
            self.first_sh_distribution,
            maximum_distance,
        )
        self.axes[0].imshow(
            all_convolved_data,
            origin="upper",
            cmap="hot",
            interpolation="nearest",
            extent=[-350, 350, 350, -350],
        )
        self.axes[1].imshow(
            first_convolved_data,
            origin="upper",
            cmap="hot",
            interpolation="nearest",
            extent=[-350, 350, 350, -350],
        )
        self.popout_axes[0].imshow(
            all_convolved_data,
            origin="upper",
            cmap="hot",
            interpolation="nearest",
            extent=[-350, 350, 350, -350],
        )
        self.popout_axes[1].imshow(
            first_convolved_data,
            origin="upper",
            cmap="hot",
            interpolation="nearest",
            extent=[-350, 350, 350, -350],
        )
        overall_optimal_coords = divmod(np.argmax(all_convolved_data), 701)
        overall_optimal_coords = (
            overall_optimal_coords[1] - 350,
            overall_optimal_coords[0] - 350,
        )
        display_text = (
            "Highest Probability Coordinates:\n"
            f"Overall: {overall_optimal_coords[0]} {overall_optimal_coords[1]} Score: {np.max(all_convolved_data)*100:.02f}%"
        )
        self.axes[0].plot(
            *overall_optimal_coords,
            marker="*",
            c="green",
        )
        self.popout_axes[0].plot(
            *overall_optimal_coords,
            marker="*",
            c="green",
        )
        for quadrant, name in enumerate(("--", "-+", "+-", "++")):
            z_start = (quadrant & 1) * 350
            x_start = (quadrant >> 1) * 350
            quadrant_data = all_convolved_data[
                z_start : z_start + 350,
                x_start : x_start + 350,
            ]
            quadrant_optimal_coords = divmod(
                np.argmax(quadrant_data),
                quadrant_data.shape[1],
            )
            quadrant_optimal_coords = (
                quadrant_optimal_coords[1] - 350 + x_start,
                quadrant_optimal_coords[0] - 350 + z_start,
            )
            display_text += f"\n{name}: {quadrant_optimal_coords[0]}, {quadrant_optimal_coords[1]} {np.max(quadrant_data)*100:.02f}%"
            if quadrant_optimal_coords == overall_optimal_coords:
                continue
            self.axes[0].plot(
                *quadrant_optimal_coords,
                marker="o",
                c="green",
            )
            self.popout_axes[0].plot(
                *quadrant_optimal_coords,
                marker="o",
                c="green",
            )
        self.coords_display.configure(text=display_text)
        self.canvas.draw()
        if self.popout_coords_display is not None:
            self.popout_coords_display.configure(text=display_text)
        if self.popout_canvas is not None:
            self.popout_canvas.draw()

    def maximum_distance_handler(self, distance):
        """Handler to be called any time the maximum distance changes"""
        distance = round(distance)
        self.maximum_distance_label.configure(text=f"Distance: {distance}")
        self.draw_heatmap(new_data=False)

    def key_press_handler(self, key):
        """Handler to be called on every new keypress"""
        key = self.keypress_listener.canonical(key)
        self.held_keys[key] = True
        self.logger.debug("%r pressed", key)
        if self.keybind_window is not None:
            if self.keybind_window.active_button is not None:
                self.keybind_window.set_active_keybind(
                    tuple(k for k, v in self.held_keys.items() if v)
                )
        else:
            for setting, keycombo in self.config.get("keybinds", {}).items():
                if all(self.held_keys[key] for key in keycombo):
                    if setting == "Reset":
                        self.divine_condition_list.clear()
                    elif setting == "Toggle Clipboard Listener":
                        self.clipboard_listener.listening = (
                            not self.clipboard_listener.listening
                        )

    def key_release_handler(self, key):
        """Handler to be called on every key release"""
        key = self.keypress_listener.canonical(key)
        self.held_keys[key] = False
        self.logger.debug("%r released", key)

    def clipboard_handler(self, clipboard):
        """Handler to be called every time the clipboard contents change"""
        self.logger.debug("New clipboard: %r", clipboard)
        # f3+i
        if clipboard.startswith("/setblock"):
            self.logger.info("f3+i detected, %r", clipboard)
            _, x, _, z, full_block = clipboard.split(" ")
            x, z = int(x), int(z)
            block_name, *_ = full_block.split("[")
            if block_name == "minecraft:chest":
                self.logger.info(
                    "Buried treasure logged chunk_x=%d, chunk_z=%d", x >> 4, z >> 4
                )
                self.divine_condition_list.add_buried_treasure_condition(x >> 4, z >> 4)
            elif 0 <= x <= 15 and 0 <= z <= 15:
                if "log" in block_name:
                    self.logger.info("10%% 80k decorator logged z=%d", z)
                    self.divine_condition_list.add_chance_decorator_condition(z)
                elif block_name in (
                    "minecraft:bone_block",
                    "minecraft:soul_sand",
                    "minecraft:soul_soil",
                ):
                    self.logger.info("Nether fossil logged x=%d", x)
                    self.divine_condition_list.add_nether_fossil_condition(x)
                elif block_name in (
                    "minecraft:clay",
                    "minecraft:gravel",
                    "minecraft:sand",
                ):
                    self.logger.info("60k %s disk logged x=%d", block_name, x)
                    self.divine_condition_list.add_disk_decorator_condition(x)
                else:
                    self.logger.info("80k decorator logged %d", x)
                    self.divine_condition_list.add_decorator_condition(x)
        elif clipboard.startswith("/execute"):
            _, _, _, _, _, _, _, _, _, yaw, _ = clipboard.split(" ")
            yaw = float(yaw) % 360
            yaw = yaw if yaw <= 180.0 else yaw - 360
            if yaw > 135 or yaw < -135:
                portal_orientation = 1
            elif yaw <= -45:
                portal_orientation = 0
            elif yaw <= 45:
                portal_orientation = 3
            elif yaw <= 135:
                portal_orientation = 2
            first_portal_logged = False
            # check all conditions for a rand(4) and assume its portal orientation
            for condition in self.divine_condition_list.conditions:
                if condition.int_maximum == 4:
                    first_portal_logged = True
                    break
            direction = ("East", "North", "West", "South")[portal_orientation]
            if not first_portal_logged:
                self.logger.info("First Portal orientation logged %s", direction)
                self.divine_condition_list.add_condition(
                    build_first_portal_condition(portal_orientation),
                    name=f"First Portal {direction}",
                    display_float_rand=False,
                    display_int_rand=False,
                    display_salt=False,
                )
            else:
                self.logger.info("Third Portal orientation logged %s", direction)
                self.divine_condition_list.add_condition(
                    build_third_portal_condition(portal_orientation),
                    name=f"Third Portal {direction}",
                    display_float_rand=False,
                    display_int_rand=False,
                    display_salt=False,
                )


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
