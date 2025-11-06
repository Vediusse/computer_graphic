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

        # Создаем сетку точек для расчета
        x_coords = np.linspace(x_min, x_max, width_res)
        y_coords = np.linspace(y_min, y_max, height_res)

        # Создаем 2D сетку координат для каждой точки
        # Meshgrid возвращает массивы X и Y, где X - это x_coords повторяющийся по строкам,
        # а Y - это y_coords повторяющийся по столбцам.
        # Мы хотим, чтобы Y соответствовал строкам изображения, X - столбцам.
        # Традиционно imshow отображает так, что строки - это Y, столбцы - это X.
        # Поэтому Y должен меняться по вертикали, X по горизонтали.
        # Для удобства представления итогового изображения,
        # часто ось Y в изображении (строки) соответствует y_coords,
        # а ось X (столбцы) соответствует x_coords.
        # Поэтому мы поменяем местами x_coords и y_coords для meshgrid.
        # Или, если Y идет сверху вниз в изображении, то y_coords должен быть инвертирован.
        # Давайте сделаем так: Y_grid - это Y координаты для каждой строки, X_grid - для каждого столбца.

        # Так как в изображении y-координата обычно растет вниз,
        # а в декартовой системе вверх, имеет смысл инвертировать y_coords для более интуитивной визуализации
        # или просто принять, что нижняя часть изображения это y_min.
        # Для данной задачи не сказано о направлении Y, так что пусть y_min будет снизу.
        # Это значит, что y_coords будет от y_min до y_max.

        # Более правильный подход для imshow:
        # X - столбцы (width_res), Y - строки (height_res)
        # Поэтому X_grid будет иметь размер (height_res, width_res)
        # Y_grid будет иметь размер (height_res, width_res)
        X_grid, Y_grid = np.meshgrid(x_coords, y_coords)  # Y_grid[i,j] - y-coord для i-ой строки, j-го столбца

        illumination_map = np.zeros((height_res, width_res))

        # Проверка на Z_L (должно быть > 0)
        if light_pos_z <= 0:
            raise ValueError("Координата Z источника света (zL) должна быть строго больше нуля.")

        # Расчет для каждой точки в сетке
        # Используем векторизованные операции NumPy для скорости
        dx = X_grid - light_pos_x
        dy = Y_grid - light_pos_y
        dz = -light_pos_z  # Расстояние по Z от плоскости до источника, если плоскость Z=0

        # Расстояние от источника до каждой точки
        r_squared = dx ** 2 + dy ** 2 + dz ** 2
        r = np.sqrt(r_squared)

        # Косинус угла падения (zL / r)
        # Добавляем маленькое значение к r_squared, чтобы избежать деления на ноль,
        # хотя в данном случае r_squared не будет нулем, если zL > 0.
        cos_theta = light_pos_z / r

        # Расчет освещенности
        # E = I0 * cos(theta) / r^2 = I0 * (zL / r) / r^2 = I0 * zL / r^3
        # Избегаем деления на ноль, если r_squared = 0 (что не произойдет, если zL > 0)
        # Для r=0 illumination будет бесконечным, но мы контролируем zL > 0,
        # поэтому r всегда будет > 0.
        illumination_map = (light_intensity_I0 * light_pos_z) / (r ** 3)

        # Применение круговой маски
        # Расстояние от каждой точки до центра круга
        dist_to_center_squared = (X_grid - circle_center_x) ** 2 + \
                                 (Y_grid - circle_center_y) ** 2

        # Если точка вне круга, освещенность = 0
        illumination_map[dist_to_center_squared > circle_radius ** 2] = 0

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
            return np.zeros_like(illumination_map, dtype=np.uint8)  # Если все нули, возвращаем все нули

        normalized_map = (illumination_map / max_val) * 255
        return normalized_map.astype(np.uint8)

    def get_cross_section(self, illumination_map, circle_center_x_px, circle_center_y_px, width_res, height_res):
        """
        Получает данные для графика сечения через центр заданной области.
        Сечение берется по горизонтали или вертикали через центр.

        Параметры:
        ----------
        illumination_map : numpy.ndarray
            Массив освещенности.
        circle_center_x_px, circle_center_y_px : int
            Координаты центра круга в пикселях.
        width_res, height_res : int
            Разрешение изображения по ширине и высоте в пикселях.

        Возвращает:
        ----------
        tuple: (numpy.ndarray, numpy.ndarray)
            Массив значений освещенности вдоль сечения и соответствующие x-координаты.
        """

        # Мы можем взять сечение через центр области изображения, а не обязательно через центр круга.
        # "график сечения, проходящего через центр заданной области"
        # Центр заданной области (в пикселях) это (width_res // 2, height_res // 2)

        center_row = height_res // 2
        center_col = width_res // 2

        # Горизонтальное сечение
        horizontal_section = illumination_map[center_row, :]

        return horizontal_section, np.arange(width_res)