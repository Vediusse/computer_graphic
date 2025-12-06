import numpy as np


class SphereBrightnessCalculator:
    def __init__(self):
        pass

    def calculate_brightness(
            self,
            screen_width_mm, screen_height_mm,
            img_width_res, img_height_res,
            observer_pos_mm,
            sphere_center_mm, sphere_radius_mm,
            light_sources_data_mm,  # Список массивов [xL, yL, zL, I0]
            ambient_coeff, diffuse_coeff, specular_coeff, shininess
    ):
        brightness_buffer = np.zeros((img_height_res, img_width_res), dtype=np.float32)

        # 1. Переводим все входные параметры геометрии в метры для расчетов
        observer_pos_m = observer_pos_mm / 1000.0
        sphere_center_m = sphere_center_mm / 1000.0
        sphere_radius_m = sphere_radius_mm / 1000.0

        light_sources_data_m = []
        for light_data_mm in light_sources_data_mm:
            light_pos_m = light_data_mm[:3] / 1000.0  # x,y,z в метры
            light_intensity_I0 = light_data_mm[3]  # I0 уже в Вт/ср
            light_sources_data_m.append(np.array([light_pos_m[0], light_pos_m[1], light_pos_m[2], light_intensity_I0]))

        # Параметры виртуального экрана
        # Экран находится в Z-плоскости центра сферы (для центрирования)
        # Это допущение, которое вы сделали. Если нужно, его можно изменить.
        screen_z_m = sphere_center_m[2]

        screen_width_m = screen_width_mm / 1000.0
        screen_height_m = screen_height_mm / 1000.0

        # Левый верхний угол экрана, центрированный на (sphere_center_m[0], sphere_center_m[0])
        # Обратите внимание: центрирование по Y также должно быть по sphere_center_m[1]
        screen_left_x_m = sphere_center_m[0] - screen_width_m / 2.0
        screen_top_y_m = sphere_center_m[1] + screen_height_m / 2.0  # Y увеличивается вверх

        for y in range(img_height_res):
            for x in range(img_width_res):
                # Координаты центра текущего пикселя на экране в метрах
                pixel_x_m = screen_left_x_m + (x + 0.5) * (screen_width_m / img_width_res)
                pixel_y_m = screen_top_y_m - (y + 0.5) * (screen_height_m / img_height_res)  # Y уменьшается вниз

                # Направление луча от наблюдателя через центр пикселя на экране
                ray_origin_m = observer_pos_m
                ray_target_on_screen_m = np.array([pixel_x_m, pixel_y_m, screen_z_m])
                ray_direction = self._normalize(ray_target_on_screen_m - ray_origin_m)

                point_on_sphere_m, normal_at_point = self._intersect_sphere(
                    ray_origin_m, ray_direction, sphere_center_m, sphere_radius_m
                )

                if point_on_sphere_m is not None:
                    intensity = self._calculate_blinn_phong_intensity(
                        point_on_sphere_m,
                        normal_at_point,
                        observer_pos_m,
                        light_sources_data_m,
                        ambient_coeff,
                        diffuse_coeff,
                        specular_coeff,
                        shininess
                    )
                    brightness_buffer[y, x] = intensity
                else:
                    brightness_buffer[y, x] = 0.0

        return brightness_buffer

    def _normalize(self, v):
        """Нормализует вектор. Не зависит от единиц измерения, так как это относительный вектор."""
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm

    def _intersect_sphere(self, ray_origin_m, ray_direction, sphere_center_m, sphere_radius_m):
        """
        Рассчитывает пересечение луча со сферой.
        Все входные параметры (ray_origin_m, sphere_center_m, sphere_radius_m) должны быть в метрах.
        Возвращает точку пересечения на сфере (в метрах) и нормаль к поверхности.
        """
        oc = ray_origin_m - sphere_center_m
        a = np.dot(ray_direction, ray_direction)
        b = 2.0 * np.dot(oc, ray_direction)
        c = np.dot(oc, oc) - sphere_radius_m ** 2

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return None, None  # Нет пересечения

        t1 = (-b - np.sqrt(discriminant)) / (2.0 * a)
        t2 = (-b + np.sqrt(discriminant)) / (2.0 * a)

        # Выбираем наименьшее положительное t. Epsilon для борьбы с плавающей точкой
        # Луч должен идти вперед от наблюдателя, поэтому t должно быть положительным
        t = -1.0
        EPSILON = 0.0001  # Маленькое положительное число, чтобы избежать пересечений "позади" наблюдателя

        if t1 > EPSILON:
            t = t1
        elif t2 > EPSILON:
            t = t2

        if t < 0:  # Если ни одно t не подходит (оба отрицательные или слишком малы)
            return None, None

        intersection_point_m = ray_origin_m + t * ray_direction  # Точка пересечения в метрах
        normal = self._normalize(intersection_point_m - sphere_center_m)
        return intersection_point_m, normal

    def _calculate_blinn_phong_intensity(
            self,
            point_on_sphere_m,
            normal,
            observer_pos_m,
            light_sources_data_m,
            ambient_coeff,
            diffuse_coeff,
            specular_coeff,
            shininess
    ):
        """
        Рассчитывает яркость в точке на сфере по модели Блинна-Фонга.
        Все расстояния и координаты здесь должны быть в метрах.
        """
        intensity = 0.0

        # Рассеянный свет (Ambient light) - базовая константа
        # Можно поиграться с этим значением
        BASE_AMBIENT_LIGHTING = 15.0
        intensity += ambient_coeff * BASE_AMBIENT_LIGHTING

        for light_source_data in light_sources_data_m:
            light_pos_m = light_source_data[:3]
            light_intensity_I0 = light_source_data[3]

            # Вектор от точки на сфере к источнику света
            L = self._normalize(light_pos_m - point_on_sphere_m)
            # Вектор от точки на сфере к наблюдателю
            V = self._normalize(observer_pos_m - point_on_sphere_m)

            # Диффузное отражение (Diffuse reflection)
            diffuse_factor = max(0.0, np.dot(normal, L))
            diffuse_term = diffuse_coeff * diffuse_factor

            # Зеркальное отражение (Specular reflection) - Блинн-Фонг
            H = self._normalize(L + V)  # Halfway vector
            specular_factor = max(0.0, np.dot(normal, H))
            specular_term = specular_coeff * (specular_factor ** shininess)

            distance_to_light_m = np.linalg.norm(light_pos_m - point_on_sphere_m)

            # Избегаем деления на ноль, если источник света слишком близко
            if distance_to_light_m < 0.001:  # 1 мм
                distance_to_light_m = 0.001

            attenuation = 1.0 / (distance_to_light_m ** 2)

            # Добавляем вклад от текущего источника света
            intensity += light_intensity_I0 * attenuation * (diffuse_term + specular_term)

        return intensity

    def normalize_brightness_to_image(self, brightness_map):
        """Нормирует значения яркости к диапазону 0-255."""
        max_val = np.max(brightness_map)
        if max_val == 0:
            return np.zeros_like(brightness_map, dtype=np.uint8)

        normalized_map = (brightness_map / max_val) * 255
        return normalized_map.astype(np.uint8)

    def get_sample_points_info(
            self,
            brightness_map,
            screen_width_mm, screen_height_mm,
            img_width_res, img_height_res,
            observer_pos_mm,
            sphere_center_mm, sphere_radius_mm,
            light_sources_data_mm,
            ambient_coeff, diffuse_coeff, specular_coeff, shininess,
            num_points=3
    ):
        sample_points_info = []

        visible_indices = np.argwhere(brightness_map > 0)

        if len(visible_indices) == 0:
            for _ in range(num_points):
                sample_points_info.append({
                    "pixel_coords": (0, 0),
                    "world_coords": "N/A (сфера не видна/не освещена)",
                    "brightness": 0.0
                })
            return sample_points_info

        num_to_sample = min(num_points, len(visible_indices))
        rng = np.random.default_rng()
        chosen_indices_idx = rng.choice(len(visible_indices), size=num_to_sample, replace=False)
        chosen_pixel_coords = visible_indices[chosen_indices_idx]

        observer_pos_m = observer_pos_mm / 1000.0
        sphere_center_m = sphere_center_mm / 1000.0
        sphere_radius_m = sphere_radius_mm / 1000.0

        light_sources_data_m = []
        for light_data_mm in light_sources_data_mm:
            light_pos_m = light_data_mm[:3] / 1000.0
            light_intensity_I0 = light_data_mm[3]
            light_sources_data_m.append(np.array([light_pos_m[0], light_pos_m[1], light_pos_m[2], light_intensity_I0]))

        screen_z_m = sphere_center_m[2]  # Плоскость, на которой проецируются пиксели
        screen_width_m = screen_width_mm / 1000.0
        screen_height_m = screen_height_mm / 1000.0
        screen_left_x_m = sphere_center_m[0] - screen_width_m / 2.0
        screen_top_y_m = sphere_center_m[1] + screen_height_m / 2.0

        for py, px in chosen_pixel_coords:
            pixel_x_m = screen_left_x_m + (px + 0.5) * (screen_width_m / img_width_res)
            pixel_y_m = screen_top_y_m - (py + 0.5) * (screen_height_m / img_height_res)

            ray_origin_m = observer_pos_m
            ray_target_on_screen_m = np.array([pixel_x_m, pixel_y_m, screen_z_m])
            ray_direction = self._normalize(ray_target_on_screen_m - ray_origin_m)

            point_on_sphere_m, normal_at_point = self._intersect_sphere(
                ray_origin_m, ray_direction, sphere_center_m, sphere_radius_m
            )

            intensity = 0.0
            world_coords_display = "N/A (вне сферы)"

            if point_on_sphere_m is not None:
                intensity = self._calculate_blinn_phong_intensity(
                    point_on_sphere_m,
                    normal_at_point,
                    observer_pos_m,
                    light_sources_data_m,
                    ambient_coeff,
                    diffuse_coeff,
                    specular_coeff,
                    shininess
                )
                world_coords_display = point_on_sphere_m * 1000.0  # обратно в мм для отображения

            sample_points_info.append({
                "pixel_coords": (px, py),
                "world_coords": world_coords_display,
                "brightness": intensity
            })
        return sample_points_info