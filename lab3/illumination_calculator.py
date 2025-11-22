import numpy as np


class IlluminationCalculator:
    def __init__(self):
        pass

    def calculate_illumination(self,
                               x_min, y_min, x_max, y_max,
                               width_res, height_res,
                               light_pos_x, light_pos_y, light_pos_z,
                               light_intensity_I0,
                               circle_center_x, circle_center_y, circle_radius):
        """
        Рассчитывает распределение освещенности на заданной области.

        Параметры:
        ----------
        x_min, y_min, x_max, y_max : float
            Границы области расчета в миллиметрах.
        width_res, height_res : int
            Разрешение по ширине и высоте в пикселях.
        light_pos_x, light_pos_y, light_pos_z : float
            Координаты источника света (xL, yL, zL) в миллиметрах.
        light_intensity_I0 : float
            Сила излучения I0 в Вт/ср.
        circle_center_x, circle_center_y : float
            Координаты центра круга в миллиметрах.
        circle_radius : float
            Радиус круга в миллиметрах, в пределах которого производится расчет.

        Возвращает:
        -----------
        numpy.ndarray
            Двумерный массив с рассчитанными значениями освещенности.
        """

        # *** Преобразуем все миллиметры в метры для корректного расчета Вт/м^2 ***
        x_min_m, y_min_m = x_min / 1000, y_min / 1000
        x_max_m, y_max_m = x_max / 1000, y_max / 1000

        light_pos_x_m, light_pos_y_m, light_pos_z_m = \
            light_pos_x / 1000, light_pos_y / 1000, light_pos_z / 1000

        circle_center_x_m, circle_center_y_m = \
            circle_center_x / 1000, circle_center_y / 1000
        circle_radius_m = circle_radius / 1000

        x_coords_m = np.linspace(x_min_m, x_max_m, width_res)
        y_coords_m = np.linspace(y_min_m, y_max_m, height_res)

        # Создаем 2D сетку координат. Y_grid соответствует строкам, X_grid - столбцам.
        X_grid_m, Y_grid_m = np.meshgrid(x_coords_m, y_coords_m)

        illumination_map = np.zeros((height_res, width_res))

        if light_pos_z_m <= 0:
            raise ValueError("Координата Z источника света (zL) должна быть строго больше нуля.")

        dx_m = X_grid_m - light_pos_x_m
        dy_m = Y_grid_m - light_pos_y_m
        dz_sq_m = light_pos_z_m ** 2  # dz - это zL

        # Расстояние от источника до каждой точки на плоскости (в метрах)
        r_squared_m = dx_m ** 2 + dy_m ** 2 + dz_sq_m
        r_m = np.sqrt(r_squared_m)

        # Расчет освещенности E = I0 * zL / r^3 (все в метрах, результат Вт/м^2)
        # Избегаем деления на ноль, так как r > 0 (так как zL > 0)
        illumination_map = (light_intensity_I0 * light_pos_z_m) / (r_m ** 3)

        # Применение круговой маски (координаты круга тоже в метрах)
        dist_to_center_squared_m = (X_grid_m - circle_center_x_m) ** 2 + \
                                   (Y_grid_m - circle_center_y_m) ** 2

        illumination_map[dist_to_center_squared_m > circle_radius_m ** 2] = 0

        return illumination_map

    def normalize_illumination(self, illumination_map):
        """
        Нормирует значения освещенности к диапазону 0-255.

        Параметры:
        ----------
        illumination_map : numpy.ndarray
            Массив освещенности.

        Возвращает:
        -----------
        numpy.ndarray
            Нормированный массив с значениями от 0 до 255 (целые числа).
        """
        max_val = np.max(illumination_map)
        if max_val == 0:
            return np.zeros_like(illumination_map, dtype=np.uint8)

        normalized_map = (illumination_map / max_val) * 255
        return normalized_map.astype(np.uint8)

    def get_cross_section(self, image_array, Wres, Hres, axis='horizontal'):
        """
        Извлекает горизонтальное или вертикальное сечение через центр изображения.
        Параметры:
            image_array: 2D numpy массив изображения (нормированная освещенность).
            Wres, Hres: разрешение сетки.
            axis: 'horizontal' для горизонтального сечения (Y=0), 'vertical' для вертикального (X=0).
        Возвращает:
            (numpy.ndarray, numpy.ndarray): Данные сечения и соответствующие координаты.
        """
        if image_array is None or Wres == 0 or Hres == 0:
            return np.array([]), np.array([])

        if axis == 'horizontal':
            center_row_index = Hres // 2
            section_data = image_array[center_row_index, :]
            section_coords = np.arange(Wres)
        elif axis == 'vertical':
            center_col_index = Wres // 2
            section_data = image_array[:, center_col_index]
            section_coords = np.arange(Hres)
        else:
            raise ValueError("Параметр 'axis' должен быть 'horizontal' или 'vertical'.")

        return section_data, section_coords

    def calculate_point_illumination(self, x_p, y_p, z_p,
                                     light_pos_x, light_pos_y, light_pos_z,
                                     light_intensity_I0,
                                     circle_center_x, circle_center_y, circle_radius):
        """
        Рассчитывает освещенность в одной конкретной точке (на плоскости Z=0),
        если она находится в круге.
        Все входные координаты в мм, конвертируются в метры для расчета.
        """
        # *** Преобразуем все миллиметры в метры ***
        x_p_m, y_p_m, z_p_m = x_p / 1000, y_p / 1000, z_p / 1000  # z_p всегда 0 для точки на плоскости
        light_pos_x_m, light_pos_y_m, light_pos_z_m = \
            light_pos_x / 1000, light_pos_y / 1000, light_pos_z / 1000
        circle_center_x_m, circle_center_y_m = \
            circle_center_x / 1000, circle_center_y / 1000
        circle_radius_m = circle_radius / 1000

        if light_pos_z_m <= 0:
            return 0.0  # Источник под плоскостью или на ней

        # Проверка, находится ли точка в круге (координаты круга тоже в метрах)
        dist_to_circle_center_squared_m = (x_p_m - circle_center_x_m) ** 2 + \
                                          (y_p_m - circle_center_y_m) ** 2
        if dist_to_circle_center_squared_m > circle_radius_m ** 2:
            return 0.0  # Точка вне круга

        # Расстояние от источника (light_pos_x_m, light_pos_y_m, light_pos_z_m)
        # до точки на плоскости (x_p_m, y_p_m, 0)

        # Расстояние по X, Y на плоскости, и расстояние по Z до плоскости
        dx_m = x_p_m - light_pos_x_m
        dy_m = y_p_m - light_pos_y_m
        # Здесь dz - это просто light_pos_z_m, потому что точка находится на Z=0
        # и расстояние по Z от источника до плоскости - это light_pos_z_m
        dz_m = light_pos_z_m

        r_plane_m = np.sqrt(dx_m ** 2 + dy_m ** 2 + dz_m ** 2)

        if r_plane_m == 0:  # Точка совпадает с проекцией источника на плоскость Z=0 (если zL=0), но мы уже проверили zL > 0
            return float('inf')  # Или какое-то очень большое число, если источник прямо над точкой

        # E = I0 * zL / r_plane^3
        return (light_intensity_I0 * light_pos_z_m) / (r_plane_m ** 3)