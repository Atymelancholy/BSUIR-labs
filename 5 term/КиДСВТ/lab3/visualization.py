import tkinter as tk
from tkinter import ttk, messagebox
import re


# ================== МОДЕЛЬ ОЗУ ==================
class RAMModel:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.size = rows * cols
        self.cells = [None] * self.size  # None = ещё не записано
        self.matrix_view = [[None for _ in range(cols)] for _ in range(rows)]

    def write(self, addr, value):
        if 0 <= addr < self.size:
            self.cells[addr] = value & 1
            # Обновляем матричное представление
            row, col = self.addr_to_matrix(addr)
            self.matrix_view[row][col] = value & 1

    def read(self, addr):
        if 0 <= addr < self.size:
            return self.cells[addr]
        return None

    def addr_to_matrix(self, addr):
        """Преобразует линейный адрес в координаты матрицы"""
        row = addr // self.cols
        col = addr % self.cols
        return row, col

    def matrix_to_addr(self, row, col):
        """Преобразует координаты матрицы в линейный адрес"""
        return row * self.cols + col


# ================== МОДЕЛИ НЕИСПРАВНОСТЕЙ ==================
class StuckAtFault:
    def __init__(self, addr, stuck_value):
        self.addr = addr
        self.stuck_value = stuck_value

    def apply_fault(self, ram):
        ram.write(self.addr, self.stuck_value)
        original_write = ram.write

        def stuck_write(addr, value):
            if addr == self.addr:
                ram.cells[addr] = self.stuck_value
                # Обновляем матричное представление
                row, col = ram.addr_to_matrix(addr)
                ram.matrix_view[row][col] = self.stuck_value
            else:
                original_write(addr, value)
        ram.write = stuck_write


class CouplingFault:
    def __init__(self, source_addr, target_addr):
        self.source_addr = source_addr
        self.target_addr = target_addr

    def apply_fault(self, ram):
        original_write = ram.write

        def faulty_write(addr, value):
            original_write(addr, value)
            if addr == self.source_addr:
                # если целевая ячейка ещё None — считаем, что она 0
                if ram.cells[self.target_addr] is None:
                    ram.cells[self.target_addr] = 0
                    row, col = ram.addr_to_matrix(self.target_addr)
                    ram.matrix_view[row][col] = 0
                ram.cells[self.target_addr] ^= 1
                row, col = ram.addr_to_matrix(self.target_addr)
                ram.matrix_view[row][col] ^= 1
        ram.write = faulty_write


class MultipleFaults:
    def __init__(self):
        self.faults = []

    def add_fault(self, fault):
        self.faults.append(fault)

    def apply_fault(self, ram):
        for fault in self.faults:
            fault.apply_fault(ram)


# ================== ТЕСТЫ ==================
class BaseTest:
    def __init__(self, ram):
        self.ram = ram
        self.write_phases = []
        self.generate_patterns()

    def generate_patterns(self):
        pass


class MarchTest(BaseTest):
    def generate_patterns(self):
        phase1 = ([0] * self.ram.size, [0] * self.ram.size)
        phase2 = ([1] * self.ram.size, [1] * self.ram.size)
        self.write_phases = [phase1, phase2]


class CheckerboardTest(BaseTest):
    def generate_patterns(self):
        pattern1 = [i % 2 for i in range(self.ram.size)]
        pattern2 = [1 - (i % 2) for i in range(self.ram.size)]
        self.write_phases = [(pattern1, pattern1), (pattern2, pattern2)]


class WalkingTest(BaseTest):
    def generate_patterns(self):
        size = self.ram.size
        phases = []
        for i in range(size):
            pattern = [0] * size
            pattern[i] = 1
            phases.append((pattern.copy(), pattern.copy()))
        self.write_phases = phases


class GallopingTest(BaseTest):
    def generate_patterns(self):
        size = self.ram.size
        phases = []
        # Паттерн 1: все 0, кроме одной 1
        for i in range(size):
            pattern = [0] * size
            pattern[i] = 1
            phases.append((pattern.copy(), pattern.copy()))
        # Паттерн 2: все 1, кроме одной 0
        for i in range(size):
            pattern = [1] * size
            pattern[i] = 0
            phases.append((pattern.copy(), pattern.copy()))
        self.write_phases = phases


class ButterflyTest(BaseTest):
    def generate_patterns(self):
        size = self.ram.size
        # Простой бабочковый паттерн для демонстрации
        pattern1 = []
        pattern2 = []
        for i in range(size):
            if i % 4 in [0, 3]:
                pattern1.append(0)
                pattern2.append(1)
            else:
                pattern1.append(1)
                pattern2.append(0)
        self.write_phases = [(pattern1, pattern1), (pattern2, pattern2)]


# ================== GUI ==================
class RAMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Цифровой двойник ОЗУ — 3 тестовых алгоритма")
        self.geometry("1400x900")
        self.resizable(True, True)

        self.ram_rows = 4
        self.ram_cols = 4
        self.ram = RAMModel(self.ram_rows, self.ram_cols)
        self.paused = False
        self.anim_speed = 100
        self.multiple_faults = MultipleFaults()

        # Информация о тестах
        self.tests_info = {
            "March Test": "Простой двухфазный тест: запись всех 0, затем всех 1",
            "Checkerboard Test": "Шахматный паттерн: чередование 0 и 1",
            "Walking Test": "'Шагающая' единица: поочередная установка 1 в каждой ячейке",
            "Galloping Test": "Расширенный тест: 'шагающие' 0 и 1",
            "Butterfly Test": "Бабочковый паттерн: группировка ячеек"
        }

        self.create_widgets()

    def create_widgets(self):
        # Главный контейнер с разделением на левую и правую части
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # ЛЕВАЯ ПАНЕЛЬ - Управление и линейное представление
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # ПРАВАЯ ПАНЕЛЬ - Матричное представление
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # ===== ЛЕВАЯ ПАНЕЛЬ =====
        # Конфигурация памяти
        config_frame = ttk.LabelFrame(left_frame, text="Конфигурация памяти", padding=10)
        config_frame.pack(fill="x", pady=5)

        ttk.Label(config_frame, text="Строки:").grid(row=0, column=0, sticky="w", padx=5)
        self.rows_var = tk.StringVar(value="4")
        rows_entry = ttk.Entry(config_frame, textvariable=self.rows_var, width=5)
        rows_entry.grid(row=0, column=1, padx=5)

        ttk.Label(config_frame, text="Столбцы:").grid(row=0, column=2, sticky="w", padx=5)
        self.cols_var = tk.StringVar(value="4")
        cols_entry = ttk.Entry(config_frame, textvariable=self.cols_var, width=5)
        cols_entry.grid(row=0, column=3, padx=5)

        ttk.Button(config_frame, text="Применить", command=self.update_ram_size).grid(row=0, column=4, padx=10)

        # Настройки теста
        test_frame = ttk.LabelFrame(left_frame, text="Настройки теста", padding=10)
        test_frame.pack(fill="x", pady=5)

        # Информация о количестве тестов
        test_info_frame = ttk.Frame(test_frame)
        test_info_frame.pack(fill="x", pady=5)

        ttk.Label(test_info_frame, text="Доступно тестов: 5", font=("Arial", 10, "bold"),
                  foreground="blue").pack(side="left", padx=5)

        ttk.Label(test_info_frame, text="Выберите тест:", font=("Arial", 10, "bold")).pack(side="left", padx=20)

        test_selection_frame = ttk.Frame(test_frame)
        test_selection_frame.pack(fill="x", pady=5)

        ttk.Label(test_selection_frame, text="Тест:").grid(row=0, column=0, sticky="w", padx=5)
        self.test_var = tk.StringVar(value="March Test")
        test_box = ttk.Combobox(test_selection_frame, textvariable=self.test_var,
                                values=list(self.tests_info.keys()), width=20)
        test_box.grid(row=0, column=1, sticky="ew", padx=5)
        test_box.bind('<<ComboboxSelected>>', self.show_test_info)

        # Описание теста
        self.test_info_label = ttk.Label(test_frame, text=self.tests_info["March Test"],
                                         font=("Arial", 9), wraplength=600, foreground="darkgreen")
        self.test_info_label.pack(fill="x", pady=5)

        # Управление неисправностями
        fault_frame = ttk.LabelFrame(left_frame, text="Управление неисправностями", padding=10)
        fault_frame.pack(fill="x", pady=5)

        # Тип неисправности
        ttk.Label(fault_frame, text="Тип неисправности:").grid(row=0, column=0, sticky="w", padx=5)
        self.fault_var = tk.StringVar(value="Без неисправности")
        fault_box = ttk.Combobox(fault_frame, textvariable=self.fault_var,
                                 values=["Без неисправности", "Stuck-at Fault", "Coupling Fault"],
                                 width=15)
        fault_box.grid(row=0, column=1, sticky="ew", padx=5)

        # Параметры неисправности
        ttk.Label(fault_frame, text="Адрес:").grid(row=0, column=2, sticky="w", padx=5)
        self.addr_entry = ttk.Entry(fault_frame, width=8)
        self.addr_entry.insert(0, "5")
        self.addr_entry.grid(row=0, column=3, padx=5)

        ttk.Label(fault_frame, text="Доп. адрес:").grid(row=0, column=4, sticky="w", padx=5)
        self.addr2_entry = ttk.Entry(fault_frame, width=8)
        self.addr2_entry.insert(0, "6")
        self.addr2_entry.grid(row=0, column=5, padx=5)

        # Кнопки управления неисправностями
        ttk.Button(fault_frame, text="Добавить неисправность",
                   command=self.add_fault).grid(row=0, column=6, padx=5)
        ttk.Button(fault_frame, text="Очистить все",
                   command=self.clear_faults).grid(row=0, column=7, padx=5)

        # Список активных неисправностей
        ttk.Label(fault_frame, text="Активные неисправности:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.faults_listbox = tk.Listbox(fault_frame, height=3, width=60)
        self.faults_listbox.grid(row=1, column=1, columnspan=6, sticky="ew", pady=5, padx=5)

        # Быстрая установка нескольких неисправностей
        ttk.Label(fault_frame, text="Быстрая установка (через запятую):").grid(row=2, column=0, sticky="w", padx=5)
        self.bulk_addr_entry = ttk.Entry(fault_frame, width=20)
        self.bulk_addr_entry.insert(0, "1,3,5,7")
        self.bulk_addr_entry.grid(row=2, column=1, padx=5)

        ttk.Button(fault_frame, text="Stuck-at 1",
                   command=lambda: self.add_bulk_faults(1)).grid(row=2, column=2, padx=2)
        ttk.Button(fault_frame, text="Stuck-at 0",
                   command=lambda: self.add_bulk_faults(0)).grid(row=2, column=3, padx=2)

        # Кнопки управления
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Запустить тест", command=self.start_test,
                   style="Accent.TButton").grid(row=0, column=0, padx=5)
        self.pause_btn = ttk.Button(button_frame, text="Пауза", command=self.toggle_pause)
        self.pause_btn.grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Сброс", command=self.reset_test).grid(row=0, column=2, padx=5)

        # Регулятор скорости
        speed_frame = ttk.LabelFrame(left_frame, text="Управление скоростью", padding=10)
        speed_frame.pack(fill="x", pady=5)

        # Быстрые кнопки скорости
        fast_speed_frame = ttk.Frame(speed_frame)
        fast_speed_frame.pack(fill="x", pady=5)

        ttk.Label(fast_speed_frame, text="Быстрый выбор:").grid(row=0, column=0, sticky="w", padx=5)

        ttk.Button(fast_speed_frame, text="10 мс",
                   command=lambda: self.set_speed(10)).grid(row=0, column=1, padx=2)
        ttk.Button(fast_speed_frame, text="50 мс",
                   command=lambda: self.set_speed(50)).grid(row=0, column=2, padx=2)
        ttk.Button(fast_speed_frame, text="100 мс",
                   command=lambda: self.set_speed(100)).grid(row=0, column=3, padx=2)
        ttk.Button(fast_speed_frame, text="300 мс",
                   command=lambda: self.set_speed(300)).grid(row=0, column=4, padx=2)
        ttk.Button(fast_speed_frame, text="500 мс",
                   command=lambda: self.set_speed(500)).grid(row=0, column=5, padx=2)

        # Тонкая настройка скорости
        fine_speed_frame = ttk.Frame(speed_frame)
        fine_speed_frame.pack(fill="x", pady=5)

        ttk.Label(fine_speed_frame, text="Тонкая настройка:").grid(row=0, column=0, sticky="w", padx=5)
        self.speed_scale = ttk.Scale(fine_speed_frame, from_=10, to=1000, orient="horizontal",
                                     command=self.update_speed, length=300)
        self.speed_scale.set(100)
        self.speed_scale.grid(row=0, column=1, padx=10)

        self.speed_label = ttk.Label(fine_speed_frame, text="100 мс/шаг", font=("Arial", 10))
        self.speed_label.grid(row=0, column=2, padx=10)

        # Линейное представление памяти
        linear_frame = ttk.LabelFrame(left_frame, text="Линейное представление памяти", padding=10)
        linear_frame.pack(fill="both", expand=True, pady=10)

        ttk.Label(linear_frame, text="Последовательность ячеек памяти:", font=("Arial", 10, "bold")).pack(anchor="w")

        # Canvas для линейного представления с прокруткой
        linear_canvas_frame = ttk.Frame(linear_frame)
        linear_canvas_frame.pack(fill="both", expand=True, pady=5)

        self.linear_canvas = tk.Canvas(linear_canvas_frame, height=120, bg="white", relief="sunken", bd=2)
        linear_scrollbar_x = ttk.Scrollbar(linear_canvas_frame, orient="horizontal", command=self.linear_canvas.xview)

        self.linear_canvas.configure(xscrollcommand=linear_scrollbar_x.set)

        self.linear_canvas.pack(side="top", fill="x")
        linear_scrollbar_x.pack(side="bottom", fill="x")

        # Статусная информация
        status_frame = ttk.LabelFrame(left_frame, text="Статус выполнения", padding=10)
        status_frame.pack(fill="x", pady=10)

        self.phase_label = ttk.Label(status_frame, text="Фаза: -", font=("Arial", 11, "italic"))
        self.phase_label.pack(anchor="w")

        self.status_label = ttk.Label(status_frame, text="Готов к запуску.", font=("Arial", 10))
        self.status_label.pack(anchor="w")

        self.result_label = ttk.Label(status_frame, text="", font=("Arial", 11, "bold"))
        self.result_label.pack(anchor="w", pady=5)

        # ===== ПРАВАЯ ПАНЕЛЬ =====
        # Матричное представление памяти
        matrix_frame = ttk.LabelFrame(right_frame, text="Матричное представление памяти", padding=10)
        matrix_frame.pack(fill="both", expand=True, pady=5)

        ttk.Label(matrix_frame, text="Организация памяти по строкам и столбцам:",
                  font=("Arial", 11, "bold")).pack(anchor="w", pady=5)

        # Информация о матрице
        matrix_info_frame = ttk.Frame(matrix_frame)
        matrix_info_frame.pack(fill="x", pady=5)

        ttk.Label(matrix_info_frame, text=f"Размер: {self.ram_rows}×{self.ram_cols} = {self.ram_rows*self.ram_cols} ячеек",
                  font=("Arial", 10), foreground="darkblue").pack(side="left", padx=5)

        # Фрейм для матрицы с прокруткой
        matrix_scroll_frame = ttk.Frame(matrix_frame)
        matrix_scroll_frame.pack(fill="both", expand=True, pady=10)

        # Создаем Canvas с прокруткой для матрицы
        self.matrix_canvas = tk.Canvas(matrix_scroll_frame, bg="white", relief="sunken", bd=2)

        # Прокрутка для матрицы
        matrix_scrollbar_y = ttk.Scrollbar(matrix_scroll_frame, orient="vertical", command=self.matrix_canvas.yview)
        matrix_scrollbar_x = ttk.Scrollbar(matrix_scroll_frame, orient="horizontal", command=self.matrix_canvas.xview)

        self.matrix_canvas.configure(yscrollcommand=matrix_scrollbar_y.set,
                                     xscrollcommand=matrix_scrollbar_x.set)

        self.matrix_canvas.grid(row=0, column=0, sticky="nsew")
        matrix_scrollbar_y.grid(row=0, column=1, sticky="ns")
        matrix_scrollbar_x.grid(row=1, column=0, sticky="ew")

        matrix_scroll_frame.grid_rowconfigure(0, weight=1)
        matrix_scroll_frame.grid_columnconfigure(0, weight=1)

        # Легенда
        legend_frame = ttk.Frame(right_frame)
        legend_frame.pack(fill="x", pady=10)

        ttk.Label(legend_frame, text="Легенда:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")

        colors_info = [
            ("Белая", "Не записано"),
            ("Серая", "Значение 0"),
            ("Зеленая", "Значение 1"),
            ("Красная", "Ошибка"),
            ("Желтая", "Текущая ячейка")
        ]

        for i, (color, meaning) in enumerate(colors_info):
            ttk.Label(legend_frame, text=color, foreground="black").grid(row=0, column=i*2+1, padx=5)
            ttk.Label(legend_frame, text=meaning, font=("Arial", 8)).grid(row=1, column=i*2+1, padx=5)

        # Инициализация отрисовки
        self.update_ram_size()

    def show_test_info(self, event=None):
        test_name = self.test_var.get()
        if test_name in self.tests_info:
            self.test_info_label.config(text=self.tests_info[test_name])

    def set_speed(self, speed):
        self.speed_scale.set(speed)
        self.update_speed(speed)

    def update_speed(self, val):
        self.anim_speed = int(float(val))
        if hasattr(self, 'speed_label'):
            self.speed_label.config(text=f"{self.anim_speed} мс/шаг")

    def add_fault(self):
        try:
            fault_type = self.fault_var.get()
            if fault_type == "Без неисправности":
                return

            addr = int(self.addr_entry.get())
            if addr < 0 or addr >= self.ram.size:
                raise ValueError("Адрес вне диапазона")

            if fault_type == "Stuck-at Fault":
                fault = StuckAtFault(addr, 1)
                description = f"Stuck-at-1 at address {addr}"
            elif fault_type == "Coupling Fault":
                addr2 = int(self.addr2_entry.get())
                if addr2 < 0 or addr2 >= self.ram.size:
                    raise ValueError("Второй адрес вне диапазона")
                fault = CouplingFault(addr, addr2)
                description = f"Coupling: {addr} -> {addr2}"

            self.multiple_faults.add_fault(fault)
            self.faults_listbox.insert(tk.END, description)

        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные параметры неисправности: {e}")

    def add_bulk_faults(self, stuck_value):
        try:
            addrs_text = self.bulk_addr_entry.get()
            addrs = [int(addr.strip()) for addr in addrs_text.split(',') if addr.strip()]

            for addr in addrs:
                if 0 <= addr < self.ram.size:
                    fault = StuckAtFault(addr, stuck_value)
                    self.multiple_faults.add_fault(fault)
                    description = f"Stuck-at-{stuck_value} at address {addr}"
                    self.faults_listbox.insert(tk.END, description)
                else:
                    messagebox.showwarning("Предупреждение", f"Адрес {addr} вне диапазона, пропущен")

        except ValueError as e:
            messagebox.showerror("Ошибка", "Введите корректные адреса через запятую")

    def clear_faults(self):
        self.multiple_faults = MultipleFaults()
        self.faults_listbox.delete(0, tk.END)

    def update_ram_size(self):
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
            if rows <= 0 or cols <= 0:
                raise ValueError("Размеры должны быть положительными")
            if rows * cols > 256:
                if not messagebox.askyesno("Подтверждение",
                                           f"Создать память размером {rows*cols} ячеек? Это может замедлить работу."):
                    return

            self.ram_rows = rows
            self.ram_cols = cols
            self.ram = RAMModel(rows, cols)
            self.clear_faults()
            self.draw_ram()
        except ValueError as e:
            messagebox.showerror("Ошибка", "Введите корректные размеры памяти.")

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Продолжить" if self.paused else "Пауза")

    def reset_test(self):
        self.ram = RAMModel(self.ram_rows, self.ram_cols)
        self.errors = []
        self.result_label.config(text="")
        self.status_label.config(text="Сброшено. Готов к запуску.")
        self.phase_label.config(text="Фаза: -")
        self.draw_ram()

    def draw_ram(self, highlight=None, errors=None):
        # Очищаем предыдущие отрисовки
        self.linear_canvas.delete("all")
        self.matrix_canvas.delete("all")

        size = self.ram.size

        # Линейное представление
        cell_width = 40
        total_width = size * cell_width
        self.linear_canvas.config(width=min(600, total_width), scrollregion=(0, 0, total_width, 120))

        for i, val in enumerate(self.ram.cells):
            x0, x1 = i * cell_width, (i + 1) * cell_width

            if val is None:
                color = "white"
            elif val == 1:
                color = "lightgreen"
            else:
                color = "lightgray"

            if errors and i in errors:
                color = "red"
            elif highlight == i:
                color = "yellow"

            self.linear_canvas.create_rectangle(x0, 20, x1, 80, fill=color, outline="black")
            if val is not None:
                self.linear_canvas.create_text((x0 + x1) / 2, 50, text=str(val), font=("Arial", 12, "bold"))
            self.linear_canvas.create_text((x0 + x1) / 2, 100, text=f"{i}", font=("Arial", 9))

        # Матричное представление
        cell_size = 70
        matrix_width = self.ram_cols * cell_size
        matrix_height = self.ram_rows * cell_size

        self.matrix_canvas.config(scrollregion=(0, 0, matrix_width, matrix_height),
                                  width=min(600, matrix_width),
                                  height=min(500, matrix_height))

        for row in range(self.ram_rows):
            for col in range(self.ram_cols):
                addr = self.ram.matrix_to_addr(row, col)
                val = self.ram.cells[addr]

                x0, x1 = col * cell_size, (col + 1) * cell_size
                y0, y1 = row * cell_size, (row + 1) * cell_size

                if val is None:
                    color = "white"
                elif val == 1:
                    color = "lightgreen"
                else:
                    color = "lightgray"

                if errors and addr in errors:
                    color = "red"
                elif highlight == addr:
                    color = "yellow"

                # Рисуем ячейку матрицы
                self.matrix_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black", width=2)

                # Значение ячейки
                if val is not None:
                    self.matrix_canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2 - 15,
                                                   text=str(val), font=("Arial", 16, "bold"))

                # Адрес ячейки
                self.matrix_canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2 + 15,
                                               text=f"[{row},{col}]", font=("Arial", 10))

                # Линейный адрес
                self.matrix_canvas.create_text((x0 + x1) / 2, y1 - 10,
                                               text=f"#{addr}", font=("Arial", 8))

    def start_test(self):
        self.ram = RAMModel(self.ram_rows, self.ram_cols)
        self.errors = []
        self.result_label.config(text="")
        self.status_label.config(text="Тестирование...")
        self.phase_label.config(text="Фаза: подготовка")
        self.paused = False
        self.pause_btn.config(text="Пауза")

        # Применяем все неисправности
        if self.faults_listbox.size() > 0:
            self.multiple_faults.apply_fault(self.ram)

        # Выбор теста
        test_name = self.test_var.get()
        if test_name == "March Test":
            self.test = MarchTest(self.ram)
        elif test_name == "Checkerboard Test":
            self.test = CheckerboardTest(self.ram)
        elif test_name == "Walking Test":
            self.test = WalkingTest(self.ram)
        elif test_name == "Galloping Test":
            self.test = GallopingTest(self.ram)
        elif test_name == "Butterfly Test":
            self.test = ButterflyTest(self.ram)
        else:
            self.test = MarchTest(self.ram)  # По умолчанию

        self.phase_index = 0
        self.subphase = "write"
        self.current_addr = 0
        self.draw_ram()
        self.animate_step()

    def animate_step(self):
        if self.paused:
            self.after(200, self.animate_step)
            return

        if self.phase_index >= len(self.test.write_phases):
            self.draw_ram(errors=self.errors)
            self.phase_label.config(text="Фаза: завершено")
            if self.errors:
                error_addrs = [f"{addr} ({self.ram.addr_to_matrix(addr)})" for addr in self.errors]
                self.result_label.config(text=f"Обнаружены ошибки в ячейках: {', '.join(error_addrs)}", foreground="red")
            else:
                self.result_label.config(text="Ошибок не обнаружено.", foreground="green")
            self.status_label.config(text="Тест завершён.")
            return

        write_pattern, expected_read = self.test.write_phases[self.phase_index]

        # Пишем
        if self.subphase == "write":
            self.phase_label.config(text=f"Фаза {self.phase_index + 1}: запись")
            if self.current_addr < self.ram.size:
                val = write_pattern[self.current_addr]
                row, col = self.ram.addr_to_matrix(self.current_addr)
                self.status_label.config(text=f"Запись {val} в адрес {self.current_addr} [{row},{col}]")
                self.ram.write(self.current_addr, val)
                self.draw_ram(highlight=self.current_addr)
                self.current_addr += 1
                self.after(self.anim_speed, self.animate_step)
            else:
                self.subphase = "read"
                self.current_addr = 0
                self.after(500, self.animate_step)

        # Читаем
        elif self.subphase == "read":
            self.phase_label.config(text=f"Фаза {self.phase_index + 1}: чтение")
            if self.current_addr < self.ram.size:
                expected = expected_read[self.current_addr]
                actual = self.ram.read(self.current_addr)
                row, col = self.ram.addr_to_matrix(self.current_addr)

                if actual != expected:
                    self.errors.append(self.current_addr)

                self.status_label.config(text=f"Чтение {actual} из адреса {self.current_addr} [{row},{col}] (ожидалось: {expected})")
                self.draw_ram(highlight=self.current_addr)
                self.current_addr += 1
                self.after(self.anim_speed, self.animate_step)
            else:
                self.phase_index += 1
                self.subphase = "write"
                self.current_addr = 0
                self.after(800, self.animate_step)


if __name__ == "__main__":
    app = RAMApp()
    app.mainloop()