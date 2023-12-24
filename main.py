"""Main CTk GUI to be run"""

import logging
import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numba.typed import List as TypedList
from numba import config
from pynput import keyboard

from util.clipboard import ClipboardListener
from util.conditions import (
    GenericCondition,
    build_buried_treasure_condition,
    numba_GenericCondition,
)
from util.heatmap import convolve_data, generate_data

logging.basicConfig()


def validate_thread_count(value: str) -> bool:
    """Validate if a thread count value is within the valid range"""
    return (
        not value
        or value.isdigit()
        and 1 <= int(value) <= config.NUMBA_DEFAULT_NUM_THREADS
    )


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

        self.first_sh_distribution = self.all_sh_distribution = None

        self.conditions = TypedList.empty_list(numba_GenericCondition)
        self.conditions.append(build_buried_treasure_condition(12, -1))

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
        self.blur_intensity_label = ctk.CTkLabel(self)
        self.blur_intensity_label.grid(row=row, column=0)
        self.blur_intensity_slider = ctk.CTkSlider(
            self, from_=1, to=150, command=self.blur_intensity_handler, width=400
        )
        self.blur_intensity_slider.grid(row=row, column=1)
        self.blur_intensity_slider.set(40)
        self.blur_intensity_handler(40)
        self.fig, self.axes = plt.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, self)

        row += 1
        self.canvas.get_tk_widget().grid(row=row, column=0, columnspan=2)

    def draw_heatmap(self, new_data: bool = True):
        """Draw heatmaps for the first ring of strongholds"""
        if new_data:
            sample_count, thread_count = int(self.sample_count_entry.get()), int(
                self.thread_count_entry.get()
            )
            self.logger.info(
                "Generating %d samples on %d threads with %d conditions",
                sample_count,
                thread_count,
                len(self.conditions),
            )
            progress = np.zeros(1, np.uint64)

            def update_progress():
                self.logger.info(
                    "Generated %d/%d samples (%.02f%%)",
                    progress[0],
                    sample_count,
                    progress[0] / sample_count * 100,
                )
                if progress[0] < sample_count:
                    self.after(100, update_progress)

            update_progress()
            (
                self.first_sh_distribution,
                self.all_sh_distribution,
            ) = generate_data(
                progress,
                sample_count,
                thread_count,
                self.conditions,
            )
            self.logger.info("Finished generation")
        elif self.first_sh_distribution is None:
            return
        if hasattr(self, "axes"):
            self.axes[0].imshow(
                convolve_data(
                    self.all_sh_distribution, round(self.blur_intensity_slider.get())
                ),
                origin="upper",
                cmap="hot",
                interpolation="nearest",
                extent=[-350, 350, 350, -350],
            )
            self.axes[1].imshow(
                convolve_data(
                    self.first_sh_distribution, round(self.blur_intensity_slider.get())
                ),
                origin="upper",
                cmap="hot",
                interpolation="nearest",
                extent=[-350, 350, 350, -350],
            )
            self.canvas.draw()

    def blur_intensity_handler(self, intensity):
        """Handler to be called any time the blur intensity changes"""
        intensity = round(intensity)
        self.blur_intensity_label.configure(text=f"Blur Intensity: {intensity}")
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
