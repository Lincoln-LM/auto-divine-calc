"""Main CTk GUI to be run"""

import logging
from collections import deque
from threading import Thread
from time import sleep

import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numba import config
from numba.typed import List as TypedList
from pynput import keyboard

from util.clipboard import ClipboardListener
from util.condition_widget import ConditionList
from util.conditions import numba_GenericCondition
from util.heatmap import convolve_data, generate_data

logging.basicConfig()


def validate_thread_count(value: str) -> bool:
    """Validate if a thread count value is within the valid range"""
    return (
        not value
        or value.isdigit()
        and 1 <= int(value) <= config.NUMBA_DEFAULT_NUM_THREADS
    )


class ProgressThread(Thread):
    """Thread to log progress of stronghold distribution generation"""

    def __init__(self, parent_logger, progress, sample_count):
        super().__init__(daemon=True)
        self.progress = progress
        self.logger = parent_logger.getChild("ProgressThread")
        self.sample_count = sample_count

    def run(self):
        while self.progress[0] < self.sample_count:
            self.logger.info(
                "Generated %d/%d samples (%.02f%%)",
                self.progress[0],
                self.sample_count,
                self.progress[0] / self.sample_count * 100,
            )
            sleep(0.05)


class MainApplication(ctk.CTk):
    """Main CTk GUI to be run"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("MainApplication")
        self.logger.setLevel(logging.DEBUG)
        ctk.set_appearance_mode("dark")
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
        self.title("Auto Divine Calculator")
        self.attributes("-topmost", True)

        self.first_sh_distribution = self.all_sh_distribution = None

        self.optimal_coords = None

        self.keypress_listener = keyboard.Listener(on_press=self.keypress_handler)
        self.clipboard_listener = ClipboardListener(on_change=self.clipboard_handler)

        self.keypress_listener.start()
        self.clipboard_listener.start()

        self.place_widgets()

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
        self.thread_count_entry.insert(0, "1")
        self.thread_count_entry.grid(row=row, column=1)
        self.thread_count_label = ctk.CTkLabel(self, text="Thread Count:")
        self.thread_count_label.grid(row=row, column=0)
        self.divine_condition_list = ConditionList(self, command=self.draw_heatmap)
        self.divine_condition_list.grid(row=row, column=2, rowspan=5)

        row += 1
        self.sample_count_label = ctk.CTkLabel(self, text="Sample Count:")
        self.sample_count_label.grid(row=row, column=0)
        self.sample_count_entry = ctk.CTkEntry(
            self,
            validate="all",
            validatecommand=(self.register(str.isdigit), "%P"),
        )
        self.sample_count_entry.insert(0, "100000")
        self.sample_count_entry.grid(row=row, column=1)

        row += 1
        self.maximum_distance_label = ctk.CTkLabel(self)
        self.maximum_distance_label.grid(row=row, column=0)
        self.maximum_distance_slider = ctk.CTkSlider(
            self, from_=1, to=2000, command=self.maximum_distance_handler, width=400
        )
        self.maximum_distance_slider.grid(row=row, column=1)
        self.maximum_distance_slider.set(500)
        self.maximum_distance_handler(500)
        self.fig, self.axes = plt.subplots(1, 2)

        row += 1
        self.regenerated_button = ctk.CTkButton(
            self,
            width=300,
            text="Regenerate Stronghold Distribution",
            command=self.draw_heatmap,
        )
        self.regenerated_button.grid(row=row, column=0, columnspan=2)

        row += 1
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=row, column=0, columnspan=2)

        row += 1
        self.coords_display = ctk.CTkLabel(self, text="")
        self.coords_display.grid(row=row, column=0, columnspan=2)

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
            progress = np.zeros(1, np.uint64)

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
        self.coords_display.configure(text=display_text)
        self.canvas.draw()

    def maximum_distance_handler(self, distance):
        """Handler to be called any time the maximum distance changes"""
        distance = round(distance)
        self.maximum_distance_label.configure(text=f"Distance: {distance}")
        self.draw_heatmap(new_data=False)

    def keypress_handler(self, key):
        """Handler to be called on every new keypress"""
        self.logger.debug("%r pressed", key)
        if key == keyboard.KeyCode.from_char("-"):
            self.draw_heatmap()

    def clipboard_handler(self, clipboard):
        """Handler to be called every time the clipboard contents change"""
        # TODO: f3i/f3c handling
        self.logger.debug("New clipboard: %r", clipboard)


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
