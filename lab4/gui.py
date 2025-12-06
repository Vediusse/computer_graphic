import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QFormLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTextEdit, QFileDialog, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
import numpy as np
from PIL import Image

# !!! Убедитесь, что sphere_brightness_calculator.py находится в том же каталоге
from sphere_brightness_calculator import SphereBrightnessCalculator


class SphereBrightnessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчет Яркости на Сфере (Блинн-Фонг)")
        self.setGeometry(100, 100, 900, 800)

        self.calculator = SphereBrightnessCalculator()
        self.raw_brightness_data = None
        self.normalized_brightness_image = None

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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)

        layout = QVBoxLayout(scroll_content_widget)

        # Секция "Параметры Экрана"
        screen_group = QGroupBox("Параметры Экрана (мм)")
        screen_form_layout = QFormLayout(screen_group)
        self.entry_screen_W = QLineEdit("1000")  # Квадратный экран по умолчанию
        self.entry_screen_H = QLineEdit("1000")
        screen_form_layout.addRow("Ширина (W):", self.entry_screen_W)
        screen_form_layout.addRow("Высота (H):", self.entry_screen_H)
        layout.addWidget(screen_group)

        # Секция "Разрешение" - теперь рассчитывается автоматически, поля будут read-only
        res_group = QGroupBox("Разрешение Изображения (пиксели, авто)")
        res_form_layout = QFormLayout(res_group)
        self.entry_img_Wres = QLineEdit("500")  # Будет перезаписано
        self.entry_img_Wres.setReadOnly(True)
        self.entry_img_Hres = QLineEdit("500")  # Будет перезаписано
        self.entry_img_Hres.setReadOnly(True)
        res_form_layout.addRow("Ширина (Wres):", self.entry_img_Wres)
        res_form_layout.addRow("Высота (Hres):", self.entry_img_Hres)
        layout.addWidget(res_group)

        # Секция "Наблюдатель"
        observer_group = QGroupBox("Позиция Наблюдателя (мм)")
        observer_form_layout = QFormLayout(observer_group)
        self.entry_obs_x = QLineEdit("0")
        self.entry_obs_y = QLineEdit("0")
        self.entry_obs_z = QLineEdit("-1500")  # Наблюдатель смотрит "вперед"
        observer_form_layout.addRow("X:", self.entry_obs_x)
        observer_form_layout.addRow("Y:", self.entry_obs_y)
        observer_form_layout.addRow("Z:", self.entry_obs_z)
        layout.addWidget(observer_group)

        # Секция "Сфера"
        sphere_group = QGroupBox("Параметры Сферы (мм)")
        sphere_form_layout = QFormLayout(sphere_group)
        self.entry_sphere_cx = QLineEdit("0")
        self.entry_sphere_cy = QLineEdit("0")
        self.entry_sphere_cz = QLineEdit("300")  # Центр сферы смещен по Z
        self.entry_sphere_r = QLineEdit("250")  # Радиус сферы
        sphere_form_layout.addRow("Центр X:", self.entry_sphere_cx)
        sphere_form_layout.addRow("Центр Y:", self.entry_sphere_cy)
        sphere_form_layout.addRow("Центр Z:", self.entry_sphere_cz)
        sphere_form_layout.addRow("Радиус:", self.entry_sphere_r)
        layout.addWidget(sphere_group)

        # Секция "Источники Света" - ОБНОВЛЕННЫЕ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ
        light_group = QGroupBox("Источник Света 1 (мм, Вт/ср) - БЛИК ПО КРАЮ")
        light_form_layout = QFormLayout(light_group)
        self.entry_light1_x = QLineEdit("800")  # Сильно справа
        self.entry_light1_y = QLineEdit("100")
        self.entry_light1_z = QLineEdit("0")  # Относительно близко к Z наблюдателя/сферы, но смещен по X
        self.entry_light1_I0 = QLineEdit("6000")  # Очень высокая интенсивность для яркого блика
        light_form_layout.addRow("X:", self.entry_light1_x)
        light_form_layout.addRow("Y:", self.entry_light1_y)
        light_form_layout.addRow("Z:", self.entry_light1_z)
        light_form_layout.addRow("I0:", self.entry_light1_I0)
        layout.addWidget(light_group)

        light2_group = QGroupBox("Источник Света 2 (мм, Вт/ср) - ОСВЕЩЕНИЕ ЛЕВОЙ ПОЛОВИНЫ")
        light2_form_layout = QFormLayout(light2_group)
        self.entry_light2_x = QLineEdit("-1000")  # Сильно слева
        self.entry_light2_y = QLineEdit("0")
        self.entry_light2_z = QLineEdit("-400")  # Спереди наблюдателя, освещает лицевую часть
        self.entry_light2_I0 = QLineEdit("4000")  # Высокая интенсивность для общей освещенности
        light2_form_layout.addRow("X:", self.entry_light2_x)
        light2_form_layout.addRow("Y:", self.entry_light2_y)
        light2_form_layout.addRow("Z:", self.entry_light2_z)
        light2_form_layout.addRow("I0:", self.entry_light2_I0)
        layout.addWidget(light2_group)

        # Секция "Параметры Блинна-Фонга" - ОБНОВЛЕННЫЕ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ
        blinn_phong_group = QGroupBox("Модель Блинна-Фонга")
        bp_form_layout = QFormLayout(blinn_phong_group)
        self.entry_ambient = QLineEdit("0.35")  # Можно немного уменьшить, если общая яркость будет слишком большой
        self.entry_diffuse = QLineEdit("1.0")  # Максимальный диффуз - для хорошего освещения
        self.entry_specular = QLineEdit("0.9")  # Высокий зеркальный - для блика
        self.entry_shininess = QLineEdit("180")  # Сделаем блик чуть резче
        bp_form_layout.addRow("Рассеянный (Ka):", self.entry_ambient)
        bp_form_layout.addRow("Диффузный (Kd):", self.entry_diffuse)
        bp_form_layout.addRow("Зеркальный (Ks):", self.entry_specular)
        bp_form_layout.addRow("Блеск (n):", self.entry_shininess)
        layout.addWidget(blinn_phong_group)

        calc_button = QPushButton("Рассчитать и Визуализировать")
        calc_button.clicked.connect(self._calculate_and_visualize)
        layout.addWidget(calc_button)

        layout.addStretch(1)
        parent_widget.setLayout(QVBoxLayout())
        parent_widget.layout().addWidget(scroll_area)

    def _create_results_tab(self, parent_widget):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)

        main_layout = QVBoxLayout(scroll_content_widget)

        image_group = QGroupBox("Визуализация Яркости Сферы (2D)")
        image_layout = QVBoxLayout(image_group)

        # Создаем контейнер для изображения, который будет управлять его пропорциями
        self.image_container_widget = QWidget()
        self.image_container_layout = QHBoxLayout(self.image_container_widget)
        self.image_container_layout.addStretch(1) # Растяжка слева
        self.image_label = QLabel("Изображение сферы будет здесь")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        # Установим политику размера, чтобы QLabel мог растягиваться, но только до определенного
        # максимального размера и с учетом его встроенной логики масштабирования.
        # Фактическое масштабирование будет происходить через QPixmap.scaled()
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setMinimumSize(100, 100) # Минимальный размер для отображения
        self.image_container_layout.addWidget(self.image_label)
        self.image_container_layout.addStretch(1) # Растяжка справа
        image_layout.addWidget(self.image_container_widget)

        main_layout.addWidget(image_group)

        stats_group = QGroupBox("Статистика Яркости")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFixedHeight(200)
        stats_layout.addWidget(self.stats_text)
        main_layout.addWidget(stats_group)

        save_image_button = QPushButton("Сохранить Изображение Сферы")
        save_image_button.clicked.connect(self._save_image)
        main_layout.addWidget(save_image_button)

        main_layout.addStretch(1)
        parent_widget.setLayout(QVBoxLayout())
        parent_widget.layout().addWidget(scroll_area)

    def _get_params(self):
        try:
            # Параметры экрана
            screen_W = float(self.entry_screen_W.text())
            screen_H = float(self.entry_screen_H.text())

            # Максимальное разрешение для изображения, которое мы *генерируем*
            # Если мы хотим, чтобы сфера всегда выглядела круглой, то
            # логично генерировать изображение с соотношением сторон 1:1,
            # но это не совсем корректно, так как мы "рисуем" на плоскости экрана,
            # которая сама может иметь произвольные пропорции.
            #
            # Вместо того, чтобы жестко привязывать разрешение изображения к MAX_RES,
            # давайте сделаем его пропорциональным реальному экрану, но
            # ограничим максимальный размер.
            # Главное, чтобы пиксели были квадратными в результирующем изображении.
            #
            # НО: Если экран имеет соотношение 2:1 (W:H), и мы на нем визуализируем
            # сферу, которая проецируется на этот экран, то результат
            # *может* быть вытянут, если сама проекция вытянута.
            #
            # Если цель, чтобы *отображаемая* сфера всегда была круглой,
            # тогда нам нужно, чтобы сама картинка, которую мы генерируем,
            # имела такие пропорции, чтобы объект, проецируемый на нее,
            # выглядел кругло, либо масштабировать ее позже.
            #
            # Лучший подход:
            # 1. Сгенерировать изображение, которое логично соответствует
            #    виртуальному экрану по пропорциям.
            # 2. При отображении, масштабировать это изображение таким образом,
            #    чтобы *визуализируемый объект* (сфера) сохранял правильные пропорции.
            #    Это означает, что сам QLabel будет иметь динамические размеры,
            #    ограниченные max(width, height) и сохраняющие aspect ratio.

            # Пусть MAX_IMAGE_SIDE_PIXELS - максимальный размер по одной из сторон для генерации
            MAX_IMAGE_SIDE_PIXELS = 800

            # Расчет разрешения на основе пропорций экрана, но ограничиваем максимальной стороной
            aspect_ratio = screen_W / screen_H

            if aspect_ratio >= 1: # Ширина больше или равна высоте
                img_Wres = MAX_IMAGE_SIDE_PIXELS
                img_Hres = int(MAX_IMAGE_SIDE_PIXELS / aspect_ratio)
            else: # Высота больше ширины
                img_Hres = MAX_IMAGE_SIDE_PIXELS
                img_Wres = int(MAX_IMAGE_SIDE_PIXELS * aspect_ratio)

            # Округлим до ближайшего четного числа для избежания проблем с центрами пикселей
            img_Wres = img_Wres if img_Wres % 2 == 0 else img_Wres + 1
            img_Hres = img_Hres if img_Hres % 2 == 0 else img_Hres + 1

            # Обновим поля разрешения (они ReadOnly)
            self.entry_img_Wres.setText(str(img_Wres))
            self.entry_img_Hres.setText(str(img_Hres))

            # Наблюдатель
            obs_x = float(self.entry_obs_x.text())
            obs_y = float(self.entry_obs_y.text())
            obs_z = float(self.entry_obs_z.text())
            observer_pos = np.array([obs_x, obs_y, obs_z])

            # Сфера
            sphere_cx = float(self.entry_sphere_cx.text())
            sphere_cy = float(self.entry_sphere_cy.text())
            sphere_cz = float(self.entry_sphere_cz.text())
            sphere_center = np.array([sphere_cx, sphere_cy, sphere_cz])
            sphere_r = float(self.entry_sphere_r.text())

            # Источники света
            light_sources = []
            light1_x = float(self.entry_light1_x.text())
            light1_y = float(self.entry_light1_y.text())
            light1_z = float(self.entry_light1_z.text())
            light1_I0 = float(self.entry_light1_I0.text())
            light_sources.append(np.array([light1_x, light1_y, light1_z, light1_I0]))

            light2_x = float(self.entry_light2_x.text())
            light2_y = float(self.entry_light2_y.text())
            light2_z = float(self.entry_light2_z.text())
            light2_I0 = float(self.entry_light2_I0.text())
            light_sources.append(np.array([light2_x, light2_y, light2_z, light2_I0]))

            # Параметры Блинна-Фонга
            ambient_coeff = float(self.entry_ambient.text())
            diffuse_coeff = float(self.entry_diffuse.text())
            specular_coeff = float(self.entry_specular.text())
            shininess = float(self.entry_shininess.text())

            # --- Валидация диапазонов ---
            if not (100 <= screen_W <= 10000 and 100 <= screen_H <= 10000):
                raise ValueError("Ширина и высота экрана должны быть от 100 до 10000 мм.")
            if not (sphere_r > 0):
                raise ValueError("Радиус сферы должен быть положительным.")

            screen_z_plane = sphere_center[2] # Использование Z центра сферы как Z-плоскости экрана

            # Ближайшая и дальняя точки сферы по оси Z
            sphere_min_z = sphere_center[2] - sphere_r
            sphere_max_z = sphere_center[2] + sphere_r

            # Условия видимости и предупреждения
            if obs_z >= sphere_max_z:
                QMessageBox.warning(self, "Внимание",
                                    f"Наблюдатель (Z={obs_z:.0f}) находится за самой дальней точкой сферы (Z={sphere_max_z:.0f}). "
                                    "Сфера, скорее всего, не будет видна, если наблюдатель смотрит в сторону увеличения Z.")
            elif obs_z >= sphere_min_z:
                QMessageBox.warning(self, "Внимание",
                                    f"Наблюдатель (Z={obs_z:.0f}) находится внутри сферы (Z-диапазон: [{sphere_min_z:.0f}, {sphere_max_z:.0f}]). "
                                    "Отображение может быть некорректным.")

            # Добавлено более точное предупреждение о плоскости экрана относительно наблюдателя
            if (obs_z < screen_z_plane and sphere_max_z <= screen_z_plane) or \
                    (obs_z > screen_z_plane and sphere_min_z >= screen_z_plane):
                QMessageBox.warning(self, "Внимание",
                                    f"Вся сфера (Z-диапазон: [{sphere_min_z:.0f}, {sphere_max_z:.0f}]) находится на или за/перед плоскостью экрана (Z={screen_z_plane:.0f}). "
                                    "При наблюдателе (Z={obs_z:.0f}) смотрящем в направлении Z, сфера может быть не видна.")

            # Валидация источников света
            for i, light in enumerate(light_sources):
                if not (-10000 <= light[0] <= 10000 and -10000 <= light[1] <= 10000):
                    raise ValueError(f"Координаты xL, yL источника {i + 1} должны быть от -10000 до 10000 мм.")
                if not (-10000 <= light[
                    2] <= 10000): # Расширим Z-диапазон для источников света, чтобы можно было разместить их перед или за сферой
                    raise ValueError(f"Координата zL источника {i + 1} должна быть от -10000 до 10000 мм.")
                if not (0.01 <= light[3] <= 10000):
                    raise ValueError(f"Сила света I0 источника {i + 1} должна быть от 0.01 до 10000 Вт/ср.")

            # Валидация параметров Блинна-Фонга
            if not (0 <= ambient_coeff <= 1 and 0 <= diffuse_coeff <= 1 and 0 <= specular_coeff <= 1):
                raise ValueError("Коэффициенты Ka, Kd, Ks должны быть в диапазоне [0, 1].")
            if not (shininess > 0):
                raise ValueError("Степень блеска (n) должна быть положительной.")

            return (screen_W, screen_H, img_Wres, img_Hres,
                    observer_pos, sphere_center, sphere_r,
                    light_sources,
                    ambient_coeff, diffuse_coeff, specular_coeff, shininess)

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка Ввода", f"Произошла ошибка при расчете: {e}")
            return None

    def _calculate_and_visualize(self):
        params = self._get_params()
        if params is None:
            return

        (screen_W, screen_H, img_Wres, img_Hres,
         observer_pos, sphere_center, sphere_r,
         light_sources,
         ambient_coeff, diffuse_coeff, specular_coeff, shininess) = params

        try:
            self.raw_brightness_data = self.calculator.calculate_brightness(
                screen_W, screen_H,
                img_Wres, img_Hres,
                observer_pos, sphere_center, sphere_r,
                light_sources,
                ambient_coeff, diffuse_coeff, specular_coeff, shininess
            )

            # Нормализуем для 2D изображения (0-255)
            self.normalized_brightness_image = self.calculator.normalize_brightness_to_image(self.raw_brightness_data)

            self._display_brightness_image(self.normalized_brightness_image)

            self._update_stats_display(params)

            self.notebook.setCurrentWidget(self.results_tab) # Переключаемся на вкладку результатов

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка Расчета", f"Произошла ошибка при расчете: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная Ошибка", f"Произошла непредвиденная ошибка: {e}")

    def _display_brightness_image(self, image_array):
        height, width = image_array.shape
        q_image = QImage(image_array.data, width, height, width, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_image)

        # Определяем максимальный размер для отображения внутри контейнера image_group
        # Мы хотим, чтобы изображение заполняло пространство, но сохраняло пропорции
        # и не превышало определенного размера, чтобы избежать излишнего масштабирования.

        # Получаем доступный размер родительского виджета или группы, чтобы оценить
        # куда масштабировать
        available_size = self.image_container_widget.size()
        if available_size.isEmpty() or available_size.width() == 0 or available_size.height() == 0:
            # Если размер еще не известен (например, при первом запуске),
            # используем разумные значения по умолчанию.
            # Можно использовать sizeHint() или max (800, 800)
            target_width = 800
            target_height = 800
        else:
            target_width = available_size.width()
            target_height = available_size.height()

        # Масштабируем QPixmap с сохранением пропорций, чтобы он помещался в целевой размер
        # Qt.KeepAspectRatio - сохраняет пропорции
        # Qt.SmoothTransformation - для лучшего качества при масштабировании
        scaled_pixmap = pixmap.scaled(
            target_width, target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
        # setScaledContents(True) здесь все еще полезно, но *после* того, как мы уже
        # масштабировали Pixmap. Это может помочь с небольшими доводками, но основное
        # масштабирование должно быть сделано на QPixmap.
        # Однако, если QLabel имеет FixedSize, setScaledContents(True) будет масштабировать Pixmap
        # до этого FixedSize, даже если он был уже масштабирован.
        #
        # Лучше: если вы масштабируете Pixmap до размера, который вы хотите,
        # тогда setScaledContents(True) может быть не нужен, если вы просто
        # хотите показать Pixmap без дополнительных искажений.
        # НО, если QLabel сам меньше или большеscaled_pixmap, то setScaledContents(True)
        # будет масштабировать, potentially causing distortion.
        #
        # Самый надежный способ - это установить размер QLabel равным размеру масштабированного Pixmap
        self.image_label.setFixedSize(scaled_pixmap.size())

        # Установка политики Expanding и AlignmentCenter с растягивателями в QHBoxLayout
        # вокруг image_label заставит QLabel центрироваться и принимать его оптимальный
        # или фиксированный размер, что сохранит пропорции.
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Теперь QLabel имеет фиксированный размер масштабированного Pixmap
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Центрируем его в макете

        # self.image_container_widget.updateGeometry()
        # self.image_container_widget.parentWidget().adjustSize()
        self.image_container_widget.update() # Обновляем контейнер, чтобы перерисовка произошла


    def _update_stats_display(self, params):
        (screen_W, screen_H, img_Wres, img_Hres,
         observer_pos, sphere_center, sphere_r,
         light_sources,
         ambient_coeff, diffuse_coeff, specular_coeff, shininess) = params

        stats_output = []
        stats_output.append("--- Расчетные значения яркости (абсолютные величины) ---\n")

        # Добавим информацию о разрешении изображения в статистику
        stats_output.append(f"Генерируемое разрешение изображения: {img_Wres}x{img_Hres} пикселей\n\n")

        sample_points_info = self.calculator.get_sample_points_info(
            self.raw_brightness_data,
            screen_W, screen_H, img_Wres, img_Hres,
            observer_pos, sphere_center, sphere_r,
            light_sources,
            ambient_coeff, diffuse_coeff, specular_coeff, shininess,
            num_points=5
        )

        for i, point_data in enumerate(sample_points_info):
            stats_output.append(f"Точка {i + 1}:\n")
            stats_output.append(f"  Пиксель: {point_data['pixel_coords']}\n")
            if isinstance(point_data['world_coords'], np.ndarray):
                stats_output.append(
                    f"  Мировые коорд.: [{point_data['world_coords'][0]:.2f}, {point_data['world_coords'][1]:.2f}, {point_data['world_coords'][2]:.2f}] мм\n")
            else:
                stats_output.append(f"  Мировые коорд.: {point_data['world_coords']}\n")
            stats_output.append(f"  Яркость (абс.): {point_data['brightness']:.7f}\n")
            stats_output.append("---\n")

        # При расчете статистики игнорируем "черные" пиксели, которые не являются частью сферы
        # (т.е., где brightness_data == 0, если фон не имеет яркости).
        # Но если в calculator.py фон имеет фоновую яркость Ka * I0, то нужно
        # скорректировать эту логику. Предполагаем, что 0 - это "ничего не видно".
        brightness_values_on_sphere = self.raw_brightness_data[self.raw_brightness_data > 0]

        max_brightness = np.max(brightness_values_on_sphere) if brightness_values_on_sphere.size > 0 else 0.0
        min_brightness = np.min(brightness_values_on_sphere) if brightness_values_on_sphere.size > 0 else 0.0
        avg_brightness = np.mean(brightness_values_on_sphere) if brightness_values_on_sphere.size > 0 else 0.0

        stats_output.append(f"\nМаксимальная яркость на сфере: {max_brightness:.7f}\n")
        stats_output.append(f"Минимальная яркость на сфере (ненулевая): {min_brightness:.7f}\n")
        stats_output.append(f"Средняя яркость на сфере (ненулевая): {avg_brightness:.7f}\n")

        self.stats_text.setText("".join(stats_output))

    def _save_image(self):
        if self.normalized_brightness_image is None:
            QMessageBox.warning(self, "Нет данных", "Сначала выполните расчет для создания изображения.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение яркости сферы", "", "PNG files (*.png);;All files (*.*)"
        )
        if file_path:
            try:
                img_to_save = Image.fromarray(self.normalized_brightness_image.astype(np.uint8), mode='L')
                img_to_save.save(file_path)
                QMessageBox.information(self, "Сохранение", f"Изображение успешно сохранено в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка Сохранения", f"Не удалось сохранить изображение: {e}")
