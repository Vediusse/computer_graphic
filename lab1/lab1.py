import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

import matplotlib as mpl

# фиксируем масштабирование DPI
mpl.rcParams['figure.dpi'] = 100
mpl.rcParams['savefig.dpi'] = 100
mpl.rcParams['figure.figsize'] = (8, 4)  # дефолтный размер


DARK_CHARCOAL = "#121212"

ELECTRIC_BLUE = "#3399FF"

MAGENTA_PINK_NEON = "#B0C7DC"

SOFT_GRAY = "#E5E5E5"

DARK_SLATE = "#2A2A2A"


class ImageAnalyzerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("АНАЛИЗАТОР ИЗОБРАЖЕНИЙ")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.resizable(True, True)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure_styles()

        self.image_paths = {
            "Картинка 1": "images1.png",
            "Картинка 2": "images2.png",
            "Картинка 3": "ex.png",
        }
        self.current_image = None
        self.photo_image = None
        self.is_processing = False
        self.rgb_array = None

        self.create_widgets()
        self.load_initial_image()

        self.after(100, lambda: self.focus_force())

    def configure_styles(self):

        self.style.configure("TFrame", background=DARK_CHARCOAL)
        self.style.configure(
            "TLabel",
            background=DARK_CHARCOAL,
            foreground=SOFT_GRAY)

        self.style.configure(
            "Header.TLabel",
            background=DARK_CHARCOAL,
            foreground=ELECTRIC_BLUE,
            font=("Consolas", 32, "bold"),
            padding=[20, 15],
        )
        self.style.configure(
            "SubHeader.TLabel",
            background=DARK_SLATE,
            foreground=MAGENTA_PINK_NEON,
            font=("Consolas", 16, "bold"),
            padding=[10, 8],
        )

        self.style.configure(
            "Info.TLabel",
            background=DARK_SLATE,
            foreground=SOFT_GRAY,
            font=("Consolas", 12),
            padding=[5, 3],
            relief="flat",
            borderwidth=0,
        )
        self.style.configure(
            "InfoTitle.TLabel",
            background=DARK_SLATE,
            foreground=SOFT_GRAY,
            font=("Consolas", 12, "bold"),
            padding=[5, 3],
        )

        self.style.configure(
            "TButton",
            background=DARK_SLATE,
            foreground=ELECTRIC_BLUE,
            font=("Consolas", 13, "bold"),
            padding=[15, 10],
            relief="flat",
            borderwidth=0,
            focusthickness=3,
            focuscolor=MAGENTA_PINK_NEON,
        )
        self.style.map(
            "TButton",
            background=[
                ("active", ELECTRIC_BLUE),
                ("pressed", ELECTRIC_BLUE),
                ("disabled", "#333333"),
            ],
            foreground=[
                ("active", DARK_CHARCOAL),
                ("pressed", DARK_CHARCOAL),
                ("disabled", "#666666"),
            ],
        )

        self.style.configure(
            "Active.TButton",
            background=ELECTRIC_BLUE,
            foreground=DARK_CHARCOAL,
            font=("Consolas", 13, "bold"),
            padding=[15, 10],
        )
        self.style.map(
            "Active.TButton", background=[
                ("active", MAGENTA_PINK_NEON), ("pressed", MAGENTA_PINK_NEON)], foreground=[
                ("active", DARK_CHARCOAL), ("pressed", DARK_CHARCOAL)], )

        self.style.configure(
            "Sidebar.TFrame",
            background=DARK_SLATE,
            padding=[
                15,
                20])
        self.style.configure(
            "Content.TFrame", background=DARK_CHARCOAL, padding=[20, 15]
        )
        self.style.configure(
            "ImageDisplay.TFrame",
            background=DARK_SLATE,
            relief="flat",
            borderwidth=0)
        self.style.configure(
            "InfoDisplay.TFrame",
            background=DARK_SLATE,
            relief="flat",
            borderwidth=0)
        self.style.configure(
            "GraphDisplay.TFrame",
            background=DARK_SLATE,
            relief="flat",
            borderwidth=0)

        self.style.configure(
            "StatusBar.TLabel",
            background=DARK_SLATE,
            foreground=SOFT_GRAY,
            font=("Consolas", 11),
            padding=[15, 8],
        )
        self.style.configure(
            "TProgressbar",
            troughcolor=DARK_SLATE,
            background=ELECTRIC_BLUE,
            darkcolor=ELECTRIC_BLUE,
            lightcolor=MAGENTA_PINK_NEON,
            bordercolor=DARK_CHARCOAL,
        )

    def create_widgets(self):

        main_container = ttk.Frame(self, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.grid_rowconfigure(1, weight=1)

        main_container.grid_columnconfigure(
            0, weight=0, minsize=250
        )

        main_container.grid_columnconfigure(1, weight=1)

        header_frame = ttk.Frame(main_container, style="TFrame")
        header_frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(
                0,
                3))
        header_label = ttk.Label(
            header_frame,
            text="АНАЛИЗАТОР ИЗОБРАЖЕНИЙ <3",
            style="Header.TLabel")
        header_label.pack(side=tk.LEFT, padx=30, pady=3)

        sidebar_frame = ttk.Frame(main_container, style="Sidebar.TFrame")
        sidebar_frame.grid(
            row=1, column=0, sticky="nswe", padx=(
                15, 10), pady=15)
        sidebar_frame.grid_rowconfigure(len(self.image_paths) + 1, weight=1)

        ttk.Label(
            sidebar_frame,
            text="ВЫБОР ИЗОБРАЖЕНИЯ:",
            style="SubHeader.TLabel",
            anchor=tk.CENTER,
        ).pack(fill=tk.X, pady=(0, 25))

        self.image_buttons = {}
        for idx, (name, path) in enumerate(self.image_paths.items()):
            button = ttk.Button(
                sidebar_frame,
                text=name.upper(),
                command=lambda n=name: self.load_image_threaded(
                    self.image_paths[n],
                    n),
            )
            button.pack(fill=tk.X, pady=8, ipady=5)
            self.image_buttons[name] = button

        content_frame = ttk.Frame(main_container, style="Content.TFrame")
        content_frame.grid(
            row=1, column=1, sticky="nswe", padx=(
                10, 15), pady=15)

        content_frame.grid_columnconfigure(0, weight=1)

        content_frame.grid_columnconfigure(
            1, weight=2
        )

        content_frame.grid_rowconfigure(0, weight=2)

        content_frame.grid_rowconfigure(1, weight=1)

        image_display_frame = ttk.Frame(
            content_frame, style="ImageDisplay.TFrame", padding=15
        )
        image_display_frame.grid(
            row=0, column=0, sticky="nswe", padx=(0, 15), pady=(0, 15)
        )
        image_display_frame.grid_rowconfigure(0, weight=1)
        image_display_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ttk.Label(
            image_display_frame, background=DARK_SLATE)

        self.image_label.grid(row=0, column=0, sticky="")

        info_frame = ttk.Frame(
            content_frame,
            style="InfoDisplay.TFrame",
            padding=20)
        info_frame.grid(row=0, column=1, sticky="nswe", pady=(0, 15))
        info_frame.grid_columnconfigure(0, weight=1)

        info_frame.grid_columnconfigure(1, weight=2)

        ttk.Label(
            info_frame,
            text="ИНФОРМАЦИЯ ОБ ИЗОБРАЖЕНИИ:",
            style="SubHeader.TLabel",
            anchor=tk.CENTER,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(
                0,
                15),
            ipadx=0)

        self.info_labels = {}
        info_rows = [
            ("НАЗВАНИЕ:", "name_val"),
            ("РАЗРЕШЕНИЕ:", "resolution_val"),
            ("ФОРМАТ:", "format_val"),
            ("РАЗМЕР (PX):", "size_px_val"),
            ("РАЗМЕР (МБ):", "size_bytes_val"),
        ]
        for idx, (label_text, key) in enumerate(info_rows):
            info_frame.grid_rowconfigure(idx + 1, weight=1)
            ttk.Label(
                info_frame,
                text=label_text,
                style="InfoTitle.TLabel",
                anchor=tk.W).grid(
                row=idx + 1,
                column=0,
                sticky=tk.W,
                padx=5,
                pady=3)
            value_label = ttk.Label(
                info_frame, text="N/A", style="Info.TLabel", anchor=tk.E
            )
            value_label.grid(
                row=idx + 1, column=1, sticky=tk.EW, padx=5, pady=3
            )

            self.info_labels[key] = value_label

        info_frame.grid_rowconfigure(
            len(info_rows) + 1,
            weight=len(info_rows) + 1)

        graph_frame = ttk.Frame(
            content_frame,
            style="GraphDisplay.TFrame",
            padding=15)
        graph_frame.grid(row=1, column=0, columnspan=2, sticky="nswe")
        graph_frame.grid_rowconfigure(0, weight=1)
        graph_frame.grid_columnconfigure(0, weight=1)

        plt.style.use("dark_background")
        frame_width = self.winfo_screenwidth()
        frame_height = self.winfo_screenheight()
        print(self.winfo_fpixels('1i'))
        self.fig, self.ax = plt.subplots(
            figsize=(frame_width, frame_height / 300),
            dpi=self.winfo_fpixels('1i'),
            facecolor=DARK_SLATE
        )
        self.ax.set_facecolor(DARK_CHARCOAL)
        self.ax.tick_params(colors=SOFT_GRAY)
        self.ax.yaxis.label.set_color(SOFT_GRAY)
        self.ax.xaxis.label.set_color(SOFT_GRAY)
        self.ax.title.set_color(MAGENTA_PINK_NEON)
        self.ax.spines["left"].set_color(SOFT_GRAY)
        self.ax.spines["bottom"].set_color(SOFT_GRAY)
        self.ax.spines["right"].set_color(SOFT_GRAY)
        self.ax.spines["top"].set_color(SOFT_GRAY)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.status_bar = ttk.Label(
            self, text="ГОТОВ К РАБОТЕ", anchor=tk.W, style="StatusBar.TLabel"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress_bar = ttk.Progressbar(
            self,
            orient="horizontal",
            length=200,
            mode="indeterminate",
            style="TProgressbar",
        )
        self.progress_bar.pack_forget()

    def load_initial_image(self):

        if self.image_paths:
            first_image_name = list(self.image_paths.keys())[0]
            self.load_image_threaded(
                self.image_paths[first_image_name], first_image_name
            )

    def _on_resize(self, event):

        if self.current_image and self.photo_image:
            self._update_image_display(self.current_image)
            self.update_graph()
        self.update_idletasks()

    def _update_image_display(self, pil_image):
        self.update_idletasks()
        display_width = self.image_label.master.winfo_width()
        display_height = self.image_label.master.winfo_height()

        if display_width <= 1 or display_height <= 1:
            return

        img_width, img_height = pil_image.size

        if img_width > display_width or img_height > display_height:
            ratio = min(display_width / img_width, display_height / img_height)
            new_width = max(1, int(img_width * ratio))
            new_height = max(1, int(img_height * ratio))
            resized_image = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
        else:

            resized_image = pil_image
            new_width, new_height = img_width, img_height

        self.photo_image = ImageTk.PhotoImage(resized_image)

        self.image_label.config(image=self.photo_image)
        self.image_label.image = self.photo_image

    def load_image_threaded(self, image_path, image_name_for_button):

        if self.is_processing:
            return

        self.is_processing = True
        self.disable_interface()
        self.status_bar.config(
            text=f"ЗАГРУЗКА И АНАЛИЗ {os.path.basename(image_path).upper()}..."
        )
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress_bar.start()

        for btn_name, btn in self.image_buttons.items():
            if btn_name == image_name_for_button:
                btn.config(style="Active.TButton")
            else:
                btn.config(style="TButton")

        threading.Thread(
            target=self._perform_image_loading, args=(image_path,), daemon=True
        ).start()

    def _perform_image_loading(self, image_path):

        try:
            pil_image = Image.open(image_path)
            self.current_image = pil_image

            self.update_idletasks()

            while (
                    self.image_label.master.winfo_width() <= 1
                    or self.image_label.master.winfo_height() <= 1
            ):
                time.sleep(0.01)

            image_info = {
                "name_val": os.path.basename(image_path).upper(),
                "resolution_val": f"{pil_image.width}X{pil_image.height}",
                "format_val": pil_image.format.upper(),
                "size_px_val": f"{pil_image.width * pil_image.height} PX",
                "size_bytes_val": (
                    f"{os.path.getsize(image_path) / (1024 * 1024):.2f} MB"
                    if os.path.exists(image_path)
                    else "N/A"
                ),
            }

            self.rgb_array = np.array(pil_image.convert("RGBA"))

            self.after(0, self._complete_image_loading, image_info, image_path)

        except Exception as e:
            self.after(
                0,
                self._show_error,
                f"ОШИБКА ЗАГРУЗКИ ИЛИ АНАЛИЗА ИЗОБРАЖЕНИЯ: {e}")

    def _complete_image_loading(self, image_info, image_path):

        self._update_image_display(self.current_image)

        for key, label in self.info_labels.items():
            label.config(text=image_info.get(key, "N/A"))

        self.update_graph()

        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_bar.config(
            text=f"ИЗОБРАЖЕНИЕ '{image_info['name_val']}' ЗАГРУЖЕНО."
        )
        self.enable_interface()
        self.is_processing = False

    def update_graph(self):

        if self.rgb_array is None:
            self.ax.clear()
            self.ax.set_title("НЕТ ДАННЫХ ДЛЯ ГРАФИКА", color=SOFT_GRAY)
            self.ax.set_facecolor(DARK_CHARCOAL)
            self.fig.set_facecolor(DARK_SLATE)
            self.canvas.draw()
            return

        self.ax.clear()

        h, w, c = self.rgb_array.shape

        channels = ["КРАСНЫЙ", "ЗЕЛЕНЫЙ", "СИНИЙ"]

        if c >= 3:
            averages = [self.rgb_array[:, :, i].mean() for i in range(3)]
        else:
            averages = [self.rgb_array[:, :, i].mean() for i in range(c)]
            channels = channels[:c]

        bar_colors = ["#FF6347", "#3CB371", ELECTRIC_BLUE]

        max_avg = max(averages) if averages else 0
        y_lim_upper = max(255, max_avg * 1.1)

        p = self.ax.bar(channels,
                        averages,
                        color=bar_colors[: len(channels)],
                        alpha=0.8,
                        width=0.6)
        self.ax.set_title(
            "СРЕДНЕЕ ЗНАЧЕНИЕ КАНАЛОВ ИЗОБРАЖЕНИЯ", color=MAGENTA_PINK_NEON, fontdict={
                "family": "Arial",
                "fontsize": 14,
                "fontweight": "bold",
            }
        )


        self.ax.set_ylabel("Яркость (0-255)", color=SOFT_GRAY)
        self.ax.set_ylim(0, y_lim_upper)

        for bar in p:
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{bar.get_height():.2f}",
                ha="center",
                va="bottom",
                color=SOFT_GRAY,
                fontdict={"fontsize": 10, "fontweight": "bold"},
                clip_on=False,
            )

        self.ax.set_facecolor(DARK_CHARCOAL)
        self.fig.set_facecolor(DARK_SLATE)
        self.ax.tick_params(axis="x", colors=SOFT_GRAY)
        self.ax.tick_params(axis="y", colors=SOFT_GRAY)
        self.ax.spines["left"].set_color(SOFT_GRAY)
        self.ax.spines["bottom"].set_color(SOFT_GRAY)
        self.ax.spines["right"].set_color(SOFT_GRAY)
        self.ax.spines["top"].set_color(SOFT_GRAY)

        self.fig.tight_layout()
        self.canvas.draw()

    def disable_interface(self):

        for button in self.image_buttons.values():
            button["state"] = "disabled"

    def enable_interface(self):

        for button in self.image_buttons.values():
            button["state"] = "enabled"

    def _show_error(self, message):

        messagebox.showerror("ОШИБКА", message)
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_bar.config(text=f"ОШИБКА: {message}")
        self.enable_interface()
        self.is_processing = False


if __name__ == "__main__":
    app = ImageAnalyzerApp()
    app.mainloop()
