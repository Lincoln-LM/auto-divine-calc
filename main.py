import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MainApplication(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ctk.set_appearance_mode("dark")
        self.title("Auto Divine Calculator")

        self.button = ctk.CTkButton(self, text=":3", command=self.update_value)
        self.button.pack()
        self.fig, self.axes = plt.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

    def update_value(self):
        self.axes[0].scatter([0], [0])
        self.canvas.draw()


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
