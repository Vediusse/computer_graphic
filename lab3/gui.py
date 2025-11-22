import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QFormLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTextEdit, QFileDialog, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PIL import Image

# Убедитесь, что illumination_calculator.py находится в том же каталоге
# или доступен в PYTHONPATH
from illumination_calculator import IlluminationCalculator


class IlluminationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчет Освещенности от Точечного Источника (PyQt6)")
        self.setGeometry(100, 100, 800, 900)  # Вернемся к более простому начальному размеру окна

        self.calculator = IlluminationCalculator()
        self.raw_illumination_data = None
        self.normalized_illumination_image = None

        self._create_widgets()

    def _create_widgets(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)

        self.params_tab = QWidget()
        self.results_tab = QWidget()

        self.notebook.addTab(self.params_tab, "Параметры Расчета")
        self.notebook.addTab(self.results_tab, "Результаты")

        self._create_params_tab(self.params_tab)
        self._create_results_tab(self.results_tab)

    def _create_params_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        # Секция "Область Расчета"
        area_group = QGroupBox("Область Расчета (мм)")
        area_form_layout = QFormLayout(area_group)
        self.entry_W = QLineEdit("5000")
        self.entry_H = QLineEdit("5000")
        area_form_layout.addRow("Ширина (W):", self.entry_W)
        area_form_layout.addRow("Высота (H):", self.entry_H)
        layout.addWidget(area_group)

        # Секция "Разрешение"
        res_group = QGroupBox("Разрешение (пиксели)")
        res_form_layout = QFormLayout(res_group)
        self.entry_Wres = QLineEdit("500")
        self.entry_Hres = QLineEdit("500")
        res_form_layout.addRow("Ширина (Wres):", self.entry_Wres)
        res_form_layout.addRow("Высота (Hres):", self.entry_Hres)
        layout.addWidget(res_group)

        # Секция "Источник Света"
        light_group = QGroupBox("Источник Света (мм, Вт/ср)")
        light_form_layout = QFormLayout(light_group)
        self.entry_xL = QLineEdit("1500")
        self.entry_yL = QLineEdit("-1000")
        self.entry_zL = QLineEdit("2500")
        self.entry_I0 = QLineEdit("800")
        light_form_layout.addRow("X (xL):", self.entry_xL)
        light_form_layout.addRow("Y (yL):", self.entry_yL)
        light_form_layout.addRow("Z (zL):", self.entry_zL)
        light_form_layout.addRow("I0 (сила света):", self.entry_I0)
        layout.addWidget(light_group)

        # Секция "Круг Расчета"
        circle_group = QGroupBox("Круг Расчета (мм)")
        circle_form_layout = QFormLayout(circle_group)
        self.entry_circle_cx = QLineEdit("0")
        self.entry_circle_cy = QLineEdit("0")
        self.entry_circle_r = QLineEdit("2500")
        circle_form_layout.addRow("Центр X:", self.entry_circle_cx)
        circle_form_layout.addRow("Центр Y:", self.entry_circle_cy)
        circle_form_layout.addRow("Радиус:", self.entry_circle_r)
        layout.addWidget(circle_group)

        calc_button = QPushButton("Рассчитать и Визуализировать")
        calc_button.clicked.connect(self._calculate_and_visualize)
        layout.addWidget(calc_button)

        layout.addStretch(1)  # Заполнитель для выравнивания групп вверх

    def _create_results_tab(self, parent_widget):
        # Создаем QVBoxLayout для ВСЕХ элементов вкладки "Результаты"
        content_layout = QVBoxLayout()

        # 1. Фрейм для изображения освещенности
        image_group = QGroupBox("Распределение Освещенности")
        image_layout = QVBoxLayout(image_group)
        self.image_label = QLabel("Изображение будет здесь")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(500, 500)  # Фиксированный квадратный размер изображения
        self.image_label.setScaledContents(True)  # Важно для масштабирования содержимого
        image_layout.addWidget(self.image_label)
        content_layout.addWidget(image_group)

        # 2. Фрейм для первого графика (Горизонтальное Сечение)
        section_group_horiz = QGroupBox("График Горизонтального Сечения")
        section_layout_horiz = QVBoxLayout(section_group_horiz)
        self.fig_section_horiz = plt.Figure(figsize=(6, 4), dpi=100)  # Размер фигуры matplotlib
        self.ax_section_horiz = self.fig_section_horiz.add_subplot(111)
        self.ax_section_horiz.set_xlabel("Пиксели по горизонтали")
        self.ax_section_horiz.set_ylabel("Нормированная освещенность")
        self.ax_section_horiz.set_title("Горизонтальное сечение (Y=0)")
        self.section_canvas_horiz = FigureCanvas(self.fig_section_horiz)
        self.section_canvas_horiz.setFixedSize(600, 400)  # Фиксированный размер для холста графика
        section_layout_horiz.addWidget(self.section_canvas_horiz)
        content_layout.addWidget(section_group_horiz)

        # 3. Фрейм для второго графика (Вертикальное Сечение)
        section_group_vert = QGroupBox("График Вертикального Сечения")
        section_layout_vert = QVBoxLayout(section_group_vert)
        self.fig_section_vert = plt.Figure(figsize=(6, 4), dpi=100)  # Размер фигуры matplotlib
        self.ax_section_vert = self.fig_section_vert.add_subplot(111)
        self.ax_section_vert.set_xlabel("Пиксели по вертикали")
        self.ax_section_vert.set_ylabel("Нормированная освещенность")
        self.ax_section_vert.set_title("Вертикальное сечение (X=0)")
        self.section_canvas_vert = FigureCanvas(self.fig_section_vert)
        self.section_canvas_vert.setFixedSize(600, 400)  # Фиксированный размер для холста графика
        section_layout_vert.addWidget(self.section_canvas_vert)
        content_layout.addWidget(section_group_vert)

        # 4. Фрейм для статистики
        stats_group = QGroupBox("Статистика Освещенности")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFixedHeight(150)  # Фиксированная высота для статистики, средний размер
        stats_layout.addWidget(self.stats_text)
        content_layout.addWidget(stats_group)

        # Добавляем кнопки сохранения в конце, но их можно разместить и по-другому
        button_hbox = QHBoxLayout()
        save_image_button = QPushButton("Сохранить Изображение")
        save_image_button.clicked.connect(self._save_image)
        button_hbox.addWidget(save_image_button)

        save_section_horiz_button = QPushButton("Сохранить Горизонтальный График")
        save_section_horiz_button.clicked.connect(self._save_section_plot_horiz)
        button_hbox.addWidget(save_section_horiz_button)

        save_section_vert_button = QPushButton("Сохранить Вертикальный График")
        save_section_vert_button.clicked.connect(self._save_section_plot_vert)
        button_hbox.addWidget(save_section_vert_button)
        content_layout.addLayout(button_hbox)

        content_layout.addStretch(1)  # Заполнитель в конце

        # Оборачиваем ВЕСЬ content_layout в QScrollArea
        scroll_widget = QWidget()
        scroll_widget.setLayout(content_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        # main_results_layout - это главный макет ДЛЯ САМОЙ ВКЛАДКИ (parent_widget)
        # И в этот главный макет добавляется ТОЛЬКО QScrollArea
        main_results_layout = QVBoxLayout(parent_widget)
        main_results_layout.addWidget(scroll_area)

    def _get_params(self):
        try:
            W = float(self.entry_W.text())
            H = float(self.entry_H.text())
            Wres = int(self.entry_Wres.text())
            Hres = int(self.entry_Hres.text())
            xL = float(self.entry_xL.text())
            yL = float(self.entry_yL.text())
            zL = float(self.entry_zL.text())
            I0 = float(self.entry_I0.text())
            circle_cx = float(self.entry_circle_cx.text())
            circle_cy = float(self.entry_circle_cy.text())
            circle_r = float(self.entry_circle_r.text())

            # Валидация диапазонов
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

            # Проверка и корректировка соотношения сторон
            ratio_W_H = W / H
            ratio_Wres_Hres = Wres / Hres

            if not np.isclose(ratio_W_H, ratio_Wres_Hres, rtol=1e-5):
                # Соотношение сторон не совпадает.
                # Будем корректировать H, чтобы соответствовать W и Wres/Hres.
                new_H = W / ratio_Wres_Hres

                # Проверим, не выходит ли новое H за пределы допустимых значений
                if not (100 <= new_H <= 10000):
                    # Если новая H выходит за пределы, попробуем скорректировать W
                    new_W = H * ratio_Wres_Hres
                    if not (100 <= new_W <= 10000):
                        # Если и W не подходит, то не можем автоматически скорректировать
                        QMessageBox.critical(
                            self,
                            "Ошибка Соотношения Сторон",
                            f"Не удается автоматически скорректировать размеры W/H ({W:.1f}/{H:.1f} мм) "
                            f"для соответствия разрешению ({Wres}/{Hres}). "
                            f"Пожалуйста, измените W или H вручную так, чтобы W/H = {ratio_Wres_Hres:.2f}."
                        )
                        return None
                    else:
                        W = new_W
                        self.entry_W.setText(f"{W:.0f}")
                        QMessageBox.warning(
                            self,
                            "Корректировка Параметров",
                            "Соотношение сторон области (W/H) было изменено для соответствия разрешению (Wres/Hres). "
                            f"Новая ширина (W): {W:.0f} мм."
                        )
                else:
                    H = new_H
                    self.entry_H.setText(f"{H:.0f}")
                    QMessageBox.warning(
                        self,
                        "Корректировка Параметров",
                        "Соотношение сторон области (W/H) было изменено для соответствия разрешению (Wres/Hres). "
                        f"Новая высота (H): {H:.0f} мм."
                    )

            return W, H, Wres, Hres, xL, yL, zL, I0, circle_cx, circle_cy, circle_r

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка Ввода", f"Некорректные данные: {e}")
            return None

    def _calculate_and_visualize(self):
        params = self._get_params()
        if params is None:
            return

        W, H, Wres, Hres, xL, yL, zL, I0, circle_cx, circle_cy, circle_r = params

        x_min, x_max = -W / 2, W / 2
        y_min, y_max = -H / 2, H / 2

        try:
            self.raw_illumination_data = self.calculator.calculate_illumination(
                x_min, y_min, x_max, y_max,
                Wres, Hres,
                xL, yL, zL, I0,
                circle_cx, circle_cy, circle_r
            )

            self.normalized_illumination_image = self.calculator.normalize_illumination(self.raw_illumination_data)

            self._display_illumination_image(self.normalized_illumination_image)

            # Горизонтальное сечение
            section_horiz_data, section_horiz_coords = self.calculator.get_cross_section(
                self.normalized_illumination_image, Wres, Hres, axis='horizontal'
            )
            self._display_section_plot(self.ax_section_horiz, self.fig_section_horiz, self.section_canvas_horiz,
                                       section_horiz_data, section_horiz_coords,
                                       "Пиксели по горизонтали", "Нормированная освещенность",
                                       "Горизонтальное сечение (Y=0)")

            # Вертикальное сечение
            section_vert_data, section_vert_coords = self.calculator.get_cross_section(
                self.normalized_illumination_image, Wres, Hres, axis='vertical'
            )
            self._display_section_plot(self.ax_section_vert, self.fig_section_vert, self.section_canvas_vert,
                                       section_vert_data, section_vert_coords,
                                       "Пиксели по вертикали", "Нормированная освещенность",
                                       "Вертикальное сечение (X=0)")

            self._update_stats_display(params, x_min, y_min, x_max, y_max)

            self.notebook.setCurrentWidget(self.results_tab)  # Переключаемся на вкладку результатов

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка Расчета", f"Произошла ошибка при расчете: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная Ошибка", f"Произошла непредвиденная ошибка: {e}")

    def _display_illumination_image(self, image_array):
        height, width = image_array.shape
        q_image = QImage(image_array.data, width, height, width, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_image)

        self.image_label.setPixmap(pixmap)
        # self.image_label.setScaledContents(True) уже установлено в _create_results_tab

    def _display_section_plot(self, ax, fig, canvas, section_data, section_coords, xlabel, ylabel, title):
        ax.clear()
        ax.plot(section_coords, section_data, color='blue')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True)
        fig.tight_layout()  # Улучшаем расположение элементов графика
        canvas.draw()

    def _update_stats_display(self, params, x_min, y_min, x_max, y_max):
        W, H, Wres, Hres, xL, yL, zL, I0, circle_cx, circle_cy, circle_r = params

        stats_output = []
        stats_output.append("--- Расчетные значения освещенности (Вт/м²) ---\n")

        # 1. Центр круга
        e_center = self.calculator.calculate_point_illumination(
            circle_cx, circle_cy, 0, xL, yL, zL, I0, circle_cx, circle_cy, circle_r
        )
        stats_output.append(f"Центр круга ({circle_cx:.1f}, {circle_cy:.1f}): {e_center:.7f}\n")

        # 2. Пересечения круга с осями X и Y (в пределах круга)
        e_x_plus = self.calculator.calculate_point_illumination(
            circle_cx + circle_r, circle_cy, 0, xL, yL, zL, I0, circle_cx, circle_cy, circle_r
        )
        stats_output.append(f"Пересечение X+ ({circle_cx + circle_r:.1f}, {circle_cy:.1f}): {e_x_plus:.7f}\n")

        e_x_minus = self.calculator.calculate_point_illumination(
            circle_cx - circle_r, circle_cy, 0, xL, yL, zL, I0, circle_cx, circle_cy, circle_r
        )
        stats_output.append(f"Пересечение X- ({circle_cx - circle_r:.1f}, {circle_cy:.1f}): {e_x_minus:.7f}\n")

        e_y_plus = self.calculator.calculate_point_illumination(
            circle_cx, circle_cy + circle_r, 0, xL, yL, zL, I0, circle_cx, circle_cy, circle_r
        )
        stats_output.append(f"Пересечение Y+ ({circle_cx:.1f}, {circle_cy + circle_r:.1f}): {e_y_plus:.7f}\n")

        e_y_minus = self.calculator.calculate_point_illumination(
            circle_cx, circle_cy - circle_r, 0, xL, yL, zL, I0, circle_cx, circle_cy, circle_r
        )
        stats_output.append(f"Пересечение Y- ({circle_cx:.1f}, {circle_cy - circle_r:.1f}): {e_y_minus:.7f}\n")

        # 3. Максимальное, минимальное и среднее значения в пределах круга
        illum_values_in_circle = self.raw_illumination_data[self.raw_illumination_data > 0]

        max_illum = np.max(illum_values_in_circle) if illum_values_in_circle.size > 0 else 0.0
        min_illum = np.min(illum_values_in_circle) if illum_values_in_circle.size > 0 else 0.0
        avg_illum = np.mean(illum_values_in_circle) if illum_values_in_circle.size > 0 else 0.0

        stats_output.append(f"\nМаксимальная освещенность в круге: {max_illum:.7f}\n")
        stats_output.append(f"Минимальная освещенность в круге (ненулевая): {min_illum:.7f}\n")
        stats_output.append(f"Средняя освещенность в круге (ненулевая): {avg_illum:.7f}\n")

        self.stats_text.setText("".join(stats_output))

    def _save_image(self):
        if self.normalized_illumination_image is None:
            QMessageBox.warning(self, "Нет данных", "Сначала выполните расчет для создания изображения.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение освещенности", "", "PNG files (*.png);;All files (*.*)"
        )
        if file_path:
            try:
                img_to_save = Image.fromarray(self.normalized_illumination_image.astype(np.uint8), mode='L')
                img_to_save.save(file_path)
                QMessageBox.information(self, "Сохранение", f"Изображение успешно сохранено в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка Сохранения", f"Не удалось сохранить изображение: {e}")

    def _save_section_plot_horiz(self):
        if self.raw_illumination_data is None:
            QMessageBox.warning(self, "Нет данных",
                                "Сначала выполните расчет для создания горизонтального графика сечения.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить горизонтальный график сечения", "", "PNG files (*.png);;All files (*.*)"
        )
        if file_path:
            try:
                self.fig_section_horiz.savefig(file_path)
                QMessageBox.information(self, "Сохранение",
                                        f"Горизонтальный график сечения успешно сохранен в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка Сохранения", f"Не удалось сохранить график: {e}")

    def _save_section_plot_vert(self):
        if self.raw_illumination_data is None:
            QMessageBox.warning(self, "Нет данных",
                                "Сначала выполните расчет для создания вертикального графика сечения.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить вертикальный график сечения", "", "PNG files (*.png);;All files (*.*)"
        )
        if file_path:
            try:
                self.fig_section_vert.savefig(file_path)
                QMessageBox.information(self, "Сохранение",
                                        f"Вертикальный график сечения успешно сохранен в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка Сохранения", f"Не удалось сохранить график: {e}")


