import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from illumination_calculator import IlluminationCalculator


class IlluminationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет Освещенности от Точечного Источника")
        self.root.geometry("1400x900")  # Увеличим размер окна для лучшей компоновки

        self.calculator = IlluminationCalculator()
        self.illumination_data = None  # Для хранения рассчитанных данных освещенности
        self.image_display_canvas = None  # Для отображения изображения освещенности
        self.section_display_canvas = None  # Для отображения графика сечения

        self._create_widgets()

    def _create_widgets(self):
        # Создаем Notebook для вкладки с параметрами и вкладки для вывода
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.params_frame = ttk.Frame(self.notebook)
        self.results_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.params_frame, text="Параметры Расчета")
        self.notebook.add(self.results_frame, text="Результаты")

        self._create_params_frame(self.params_frame)
        self._create_results_frame(self.results_frame)

    def _create_params_frame(self, parent_frame):
        # Секция "Область Расчета"
        area_frame = ttk.LabelFrame(parent_frame, text="Область Расчета (мм)", padding="10")
        area_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(area_frame, text="Ширина (W):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_W = ttk.Entry(area_frame, width=10)
        self.entry_W.grid(row=0, column=1, sticky="w", pady=2)
        self.entry_W.insert(0, "5000")  # Значение по умолчанию

        ttk.Label(area_frame, text="Высота (H):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_H = ttk.Entry(area_frame, width=10)
        self.entry_H.grid(row=1, column=1, sticky="w", pady=2)
        self.entry_H.insert(0, "5000")  # Значение по умолчанию

        # Секция "Разрешение"
        res_frame = ttk.LabelFrame(parent_frame, text="Разрешение (пиксели)", padding="10")
        res_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(res_frame, text="Ширина (Wres):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_Wres = ttk.Entry(res_frame, width=10)
        self.entry_Wres.grid(row=0, column=1, sticky="w", pady=2)
        self.entry_Wres.insert(0, "500")  # Значение по умолчанию

        ttk.Label(res_frame, text="Высота (Hres):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_Hres = ttk.Entry(res_frame, width=10)
        self.entry_Hres.grid(row=1, column=1, sticky="w", pady=2)
        self.entry_Hres.insert(0, "500")  # Значение по умолчанию

        # Важно: обеспечить квадратные пиксели.
        # W / Wres = H / Hres => W * Hres = H * Wres
        # Если пользователь вводит Wres, Hres, то они должны соответствовать W и H.
        # Проще сделать так: Wres и Hres должны быть одинаковыми, если W и H одинаковые.
        # Или: W_res = W / pixel_size; H_res = H / pixel_size
        # Например, если W=1000, H=500, и Wres=200, то Hres = (500/1000)*200 = 100
        # То есть Hres = H * (Wres / W)
        # Давайте сделаем, чтобы Hres = Wres по умолчанию и W = H.
        # Либо пусть пользователь вводит Wres и Hres, а мы проверяем соотношение W/H == Wres/Hres.

        # Секция "Источник Света"
        light_frame = ttk.LabelFrame(parent_frame, text="Источник Света (мм, Вт/ср)", padding="10")
        light_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(light_frame, text="X (xL):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_xL = ttk.Entry(light_frame, width=10)
        self.entry_xL.grid(row=0, column=1, sticky="w", pady=2)
        self.entry_xL.insert(0, "0")

        ttk.Label(light_frame, text="Y (yL):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_yL = ttk.Entry(light_frame, width=10)
        self.entry_yL.grid(row=1, column=1, sticky="w", pady=2)
        self.entry_yL.insert(0, "0")

        ttk.Label(light_frame, text="Z (zL):").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_zL = ttk.Entry(light_frame, width=10)
        self.entry_zL.grid(row=2, column=1, sticky="w", pady=2)
        self.entry_zL.insert(0, "1000")  # zL > 0

        ttk.Label(light_frame, text="I0 (сила света):").grid(row=3, column=0, sticky="w", pady=2)
        self.entry_I0 = ttk.Entry(light_frame, width=10)
        self.entry_I0.grid(row=3, column=1, sticky="w", pady=2)
        self.entry_I0.insert(0, "100")  # Значение по умолчанию

        # Секция "Круг Расчета"
        circle_frame = ttk.LabelFrame(parent_frame, text="Круг Расчета (мм)", padding="10")
        circle_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(circle_frame, text="Центр X:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_circle_cx = ttk.Entry(circle_frame, width=10)
        self.entry_circle_cx.grid(row=0, column=1, sticky="w", pady=2)
        self.entry_circle_cx.insert(0, "0")  # По умолчанию центр области

        ttk.Label(circle_frame, text="Центр Y:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_circle_cy = ttk.Entry(circle_frame, width=10)
        self.entry_circle_cy.grid(row=1, column=1, sticky="w", pady=2)
        self.entry_circle_cy.insert(0, "0")  # По умолчанию центр области

        ttk.Label(circle_frame, text="Радиус:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_circle_r = ttk.Entry(circle_frame, width=10)
        self.entry_circle_r.grid(row=2, column=1, sticky="w", pady=2)
        # Радиус по умолчанию - половина меньшего из W или H
        self.entry_circle_r.insert(0, str(min(float(self.entry_W.get()), float(self.entry_H.get())) / 2))

        # Кнопка расчета
        calc_button = ttk.Button(parent_frame, text="Рассчитать и Визуализировать",
                                 command=self._calculate_and_visualize)
        calc_button.grid(row=4, column=0, padx=10, pady=15, sticky="ew")

        # Настройка растяжения столбцов
        parent_frame.grid_columnconfigure(0, weight=1)

    def _create_results_frame(self, parent_frame):
        # Фрейм для изображения освещенности
        image_frame = ttk.LabelFrame(parent_frame, text="Распределение Освещенности", padding="10")
        image_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack(expand=True, fill="both")

        # Фрейм для графика сечения
        section_frame = ttk.LabelFrame(parent_frame, text="График Сечения", padding="10")
        section_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Создаем фигуру и ось для графика Matplotlib
        self.fig_section = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax_section = self.fig_section.add_subplot(111)
        self.ax_section.set_xlabel("Пиксели по горизонтали")
        self.ax_section.set_ylabel("Нормированная освещенность")
        self.ax_section.set_title("Горизонтальное сечение через центр области")

        self.section_canvas_widget = FigureCanvasTkAgg(self.fig_section, master=section_frame)
        self.section_canvas_widget.draw()
        self.section_canvas_widget.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Кнопки для сохранения
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        save_image_button = ttk.Button(button_frame, text="Сохранить Изображение", command=self._save_image)
        save_image_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True)

        save_section_button = ttk.Button(button_frame, text="Сохранить График Сечения", command=self._save_section_plot)
        save_section_button.pack(side=tk.RIGHT, padx=5, pady=5, expand=True)

        # Настройка растяжения столбцов и строк в results_frame
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(0, weight=3)  # Изображение занимает больше места
        parent_frame.grid_rowconfigure(1, weight=2)  # График
        parent_frame.grid_rowconfigure(2, weight=0)  # Кнопки

    def _get_params(self):
        """Считывает параметры из полей ввода и проверяет их."""
        try:
            W = float(self.entry_W.get())
            H = float(self.entry_H.get())
            Wres = int(self.entry_Wres.get())
            Hres = int(self.entry_Hres.get())
            xL = float(self.entry_xL.get())
            yL = float(self.entry_yL.get())
            zL = float(self.entry_zL.get())
            I0 = float(self.entry_I0.get())
            circle_cx = float(self.entry_circle_cx.get())
            circle_cy = float(self.entry_circle_cy.get())
            circle_r = float(self.entry_circle_r.get())

            # Валидация
            if not (100 <= W <= 10000 and 100 <= H <= 10000):
                raise ValueError("Ширина и высота области должны быть от 100 до 10000 мм.")
            if not (200 <= Wres <= 800 and 200 <= Hres <= 800):
                raise ValueError("Разрешение (Wres, Hres) должно быть от 200 до 800 пикселей.")
            if not (-10000 <= xL <= 10000 and -10000 <= yL <= 10000):
                raise ValueError("Координаты xL, yL источника должны быть от -10000 до 10000 мм.")
            if not (100 <= zL <= 10000):
                raise ValueError("Координата zL источника должна быть от 100 до 10000 мм.")
            if not (0.01 <= I0 <= 10000):
                raise ValueError("Сила света I0 должна быть от 0.01 до 10000 Вт/ср.")
            if circle_r <= 0:
                raise ValueError("Радиус круга должен быть положительным.")

            # Проверка на квадратные пиксели (W/Wres == H/Hres)
            # Допустим небольшую погрешность при сравнении float
            if not np.isclose(W / Wres, H / Hres, rtol=1e-5):
                messagebox.showwarning(
                    "Несоответствие разрешения",
                    "Соотношение сторон области (W/H) не соответствует соотношению сторон разрешения (Wres/Hres). "
                    "Пиксели не будут квадратными. Рекомендуется установить Hres = H * (Wres / W)."
                )
                # Можно автоматически скорректировать Hres, но пока просто предупредим
                # self.entry_Hres.delete(0, tk.END)
                # self.entry_Hres.insert(0, str(int(H * (Wres / W))))
                # Hres = int(H * (Wres / W))

            return W, H, Wres, Hres, xL, yL, zL, I0, circle_cx, circle_cy, circle_r

        except ValueError as e:
            messagebox.showerror("Ошибка Ввода", f"Некорректные данные: {e}")
            return None

    def _calculate_and_visualize(self):
        params = self._get_params()
        if params is None:
            return

        W, H, Wres, Hres, xL, yL, zL, I0, circle_cx, circle_cy, circle_r = params

        # Область расчета: x от -W/2 до W/2, y от -H/2 до H/2
        x_min, x_max = -W / 2, W / 2
        y_min, y_max = -H / 2, H / 2

        try:
            raw_illumination = self.calculator.calculate_illumination(
                x_min, y_min, x_max, y_max,
                Wres, Hres,
                xL, yL, zL, I0,
                circle_cx, circle_cy, circle_r
            )

            # Сохраняем исходные данные освещенности для сохранения в файл
            self.illumination_data = raw_illumination.copy()

            # Нормируем для визуализации (0-255)
            normalized_illumination = self.calculator.normalize_illumination(raw_illumination)

            # Визуализация изображения
            self._display_illumination_image(normalized_illumination)

            # Визуализация графика сечения
            # Переводим центр круга в пиксельные координаты для сечения,
            # но для "центра заданной области" это не нужно, просто берем центр пиксельной сетки.
            # Если область от x_min до x_max, то 0_mm соответствует (0 - x_min) / (x_max - x_min) * Wres пикселей
            # circle_center_x_px = int(((circle_cx - x_min) / (x_max - x_min)) * Wres)
            # circle_center_y_px = int(((circle_cy - y_min) / (y_max - y_min)) * Hres) # y_min внизу, y_max вверху

            # В Matplotlib imshow обычно origin='upper', то есть y=0 это верхний край.
            # Поэтому y_coords в illumination_calculator.py идут от y_min (снизу) до y_max (сверху),
            # или от y_max (сверху) до y_min (снизу), в зависимости от того, как мы хотим отобразить.
            # Если `imshow(..., origin='lower')`, то `y_min` будет внизу.
            # Давайте примем `origin='lower'` для `imshow`.
            # В `illumination_calculator`, `Y_grid` идет от `y_min` до `y_max`.
            # Если `Y_grid` от `y_min` до `y_max` (растет), а `imshow` с `origin='lower'`
            # то `Y_grid[0, :]` соответствует `y_min`, а `Y_grid[Hres-1, :]` соответствует `y_max`.
            # Строка `center_row = Hres // 2` будет соответствовать `y = y_min + (H / Hres) * center_row`.

            # Сечение через центр изображения в пикселях:
            section_data, section_coords = self.calculator.get_cross_section(
                normalized_illumination, Wres // 2, Hres // 2, Wres, Hres
            )
            self._display_section_plot(section_data, section_coords)

            self.notebook.select(self.results_frame)  # Переключаемся на вкладку с результатами

        except ValueError as e:
            messagebox.showerror("Ошибка Расчета", f"Произошла ошибка при расчете: {e}")
        except Exception as e:
            messagebox.showerror("Неизвестная Ошибка", f"Произошла непредвиденная ошибка: {e}")

    def _display_illumination_image(self, image_array):
        """Отображает изображение освещенности в Tkinter."""
        # Убедимся, что image_array имеет правильный тип и диапазон
        image_array_scaled = np.array(image_array, dtype=np.uint8)

        # Преобразуем массив NumPy в объект PhotoImage
        img_pil = Image.fromarray(image_array_scaled, mode='L')  # 'L' для черно-белого

        # Получаем текущие размеры label для подгонки изображения
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        if label_width == 1 or label_height == 1:  # Изначальные размеры могут быть 1x1 до отрисовки
            # Если еще не отрисовано, используем размеры по умолчанию или просто не масштабируем пока
            resized_img_pil = img_pil
        else:
            # Масштабируем изображение так, чтобы оно поместилось в label, сохраняя пропорции
            img_pil.thumbnail((label_width, label_height), Image.Resampling.LANCZOS)
            resized_img_pil = img_pil

        img_tk = ImageTk.PhotoImage(resized_img_pil)

        # Обновляем изображение в Label
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk  # Сохраняем ссылку, чтобы избежать сборки мусора

    def _display_section_plot(self, section_data, section_coords):
        """Отображает график сечения."""
        self.ax_section.clear()
        self.ax_section.plot(section_coords, section_data, color='blue')
        self.ax_section.set_xlabel("Пиксели по горизонтали")
        self.ax_section.set_ylabel("Нормированная освещенность")
        self.ax_section.set_title("Горизонтальное сечение через центр области")
        self.ax_section.grid(True)
        self.section_canvas_widget.draw()

    def _save_image(self):
        if self.illumination_data is None:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет для создания изображения.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Сохранить изображение освещенности"
        )
        if file_path:
            try:
                # Нормируем для сохранения, если еще не нормировано (или берем уже нормированное)
                normalized_for_save = self.calculator.normalize_illumination(self.illumination_data)
                img_to_save = Image.fromarray(normalized_for_save, mode='L')
                img_to_save.save(file_path)
                messagebox.showinfo("Сохранение", f"Изображение успешно сохранено в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка Сохранения", f"Не удалось сохранить изображение: {e}")

    def _save_section_plot(self):
        if self.illumination_data is None:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет для создания графика сечения.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Сохранить график сечения"
        )
        if file_path:
            try:
                self.fig_section.savefig(file_path)
                messagebox.showinfo("Сохранение", f"График сечения успешно сохранен в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка Сохранения", f"Не удалось сохранить график: {e}")