import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

COLORS = {
    'bg_primary': '#F5F0FF',
    'bg_secondary': '#FFFFFF',
    'bg_light': '#F8F6FF',
    'accent_lavender': '#E6E6FF',
    'accent_light_purple': '#D4CCFF',
    'accent_purple': '#B8A3FF',
    'accent_deep_purple': '#9D87FF',
    'accent_violet': '#826CFF',
    'accent_mint': '#A3FFE6',
    'accent_rose': '#FFD4E6',
    'text_dark': '#4A4458',
    'text_medium': '#6B6580',
    'text_light': '#8C86A8',
    'border_light': '#E6E0E9',
    'bus_color': '#9D87FF',
    'controller_color': '#826CFF',
    'station_to_station_color': '#FF87B4',
    'station_broadcast_color': '#FFA343'
}


def format_hex_address(address):
    return f"0x{address:02X}"


class CRC8:
    POLYNOMIAL = 0x07

    @staticmethod
    def calculate(data):
        crc = 0
        if isinstance(data, str):
            data = data.encode('utf-8')

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRC8.POLYNOMIAL
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc


class Message:
    def __init__(self, source_addr, dest_addr, data, msg_type="unicast"):
        self.source_address = source_addr
        self.destination_address = dest_addr
        self.data = data
        self.type = msg_type
        self.length = len(data)
        self.timestamp = time.time()
        self.checksum = self.calculate_checksum()

    def calculate_checksum(self):
        packet_data = f"{self.source_address:02X}{self.destination_address:02X}{self.type}{self.length}{self.data}"
        return CRC8.calculate(packet_data)

    def verify_checksum(self):
        current_checksum = self.calculate_checksum()
        return current_checksum == self.checksum

    def get_packet_info(self):
        return (f"SRC:0x{self.source_address:02X} DST:0x{self.destination_address:02X} "
                f"TYPE:{self.type} LEN:{self.length} CRC8:0x{self.checksum:02X}")


class Station:
    def __init__(self, address, name, network, canvas, x, y):
        self.address = address
        self.name = name
        self.network = network
        self.received_messages = []
        self.running = True
        self.canvas = canvas
        self.x = x
        self.y = y
        self.visual_id = None
        self.text_id = None
        self.connection_id = None
        self.draw_station()

    def draw_station(self):
        if self.visual_id:
            self.canvas.delete(self.visual_id)
            self.canvas.delete(self.text_id)
            self.canvas.delete(self.connection_id)

        self.visual_id = self.canvas.create_rectangle(
            self.x - 30, self.y - 20, self.x + 30, self.y + 20,
            fill=COLORS['accent_purple'], outline=COLORS['border_light'], width=2,
            stipple='gray50'
        )

        self.text_id = self.canvas.create_text(
            self.x, self.y,
            text=f"{self.name}\n{format_hex_address(self.address)}",
            fill='white',
            font=('Arial', 8, 'bold'),
            justify='center'
        )

        self.connection_id = self.canvas.create_line(
            self.x, self.y + 20, self.x, 120,
            width=2, fill=COLORS['accent_light_purple'], dash=(2, 2)
        )

    def highlight_station(self, color=COLORS['accent_mint']):
        if self.visual_id:
            original_color = COLORS['accent_purple']
            self.canvas.itemconfig(self.visual_id, fill=color)
            self.canvas.after(800, lambda: self.canvas.itemconfig(self.visual_id, fill=original_color))

    def receive_message(self, message):
        should_receive = False

        if message.type == "broadcast" or message.destination_address == 0xFF:
            should_receive = True
        elif message.type == "station_broadcast" and message.destination_address == 0xFE:
            if message.source_address != self.address:
                should_receive = True
        elif message.destination_address == self.address:
            should_receive = True

        if should_receive:
            if not message.verify_checksum():
                source_name = "Контроллер" if message.source_address == 0x00 else f"Станция {format_hex_address(message.source_address)}"
                error_msg = f" {self.name} ОШИБКА CRC8! Пакет поврежден от {source_name}"
                print(error_msg)
                return False

            self.received_messages.append(message)
            source_name = "Контроллер" if message.source_address == 0x00 else f"Станция {format_hex_address(message.source_address)}"
            success_msg = f" {self.name} ({format_hex_address(self.address)}) получила от {source_name}: {message.data}"
            print(success_msg)
            print(f"    Инфо пакета: {message.get_packet_info()}")

            if message.type == "station_broadcast":
                self.highlight_station(COLORS['station_broadcast_color'])
            else:
                self.highlight_station()
            return True

        return False

    def send_message(self, dest_addr, data, msg_type="unicast"):
        print(f" {self.name} отправляет {msg_type} сообщение для {format_hex_address(dest_addr)}: {data}")

        if msg_type == "station_broadcast":
            self.highlight_station(COLORS['station_broadcast_color'])
        else:
            self.highlight_station(COLORS['station_to_station_color'])

        return self.network.send_message(self.address, dest_addr, data, msg_type, self.x)

    def stop(self):
        self.running = False


class NetworkController:
    def __init__(self, network, canvas, x, y):
        self.network = network
        self.canvas = canvas
        self.x = x
        self.y = y
        self.address = 0x00
        self.visual_id = None
        self.text_id = None
        self.connection_id = None
        self.draw_controller()

    def draw_controller(self):
        self.visual_id = self.canvas.create_rectangle(
            self.x - 25, self.y - 15, self.x + 25, self.y + 15,
            fill=COLORS['controller_color'], outline=COLORS['border_light'], width=2,
            stipple='gray50'
        )

        self.text_id = self.canvas.create_text(
            self.x, self.y,
            text=f" Контроллер",
            fill='white',
            font=('Arial', 7, 'bold')
        )

        self.connection_id = self.canvas.create_line(
            self.x, self.y + 15, self.x, 120,
            width=2, fill=COLORS['accent_violet']
        )

    def highlight_controller(self, color=COLORS['accent_deep_purple']):
        if self.visual_id:
            original_color = COLORS['controller_color']
            self.canvas.itemconfig(self.visual_id, fill=color)
            self.canvas.after(500, lambda: self.canvas.itemconfig(self.visual_id, fill=original_color))

    def send_message(self, dest_addr, data, msg_type="unicast"):
        print(f" Контроллер отправляет {msg_type} сообщение для {format_hex_address(dest_addr)}: {data}")
        self.highlight_controller()
        return self.network.send_message(self.address, dest_addr, data, msg_type, self.x)


class Network:
    def __init__(self, canvas, app=None):
        self.stations = []
        self.lock = threading.Lock()
        self.canvas = canvas
        self.bus_line = None
        self.controller = None
        self.app = app
        self.draw_bus_topology()

    def add_station(self, station):
        self.stations.append(station)

    def set_controller(self, controller):
        self.controller = controller

    def draw_bus_topology(self):
        if self.bus_line:
            self.canvas.delete(self.bus_line)

        self.bus_line = self.canvas.create_line(
            50, 120, 750, 120,
            width=8, fill=COLORS['bus_color']
        )

        self.canvas.create_rectangle(45, 115, 755, 125, fill=COLORS['accent_lavender'], outline='')

        self.canvas.create_text(400, 105, text=" ОБЩАЯ ШИНА ДАННЫХ ", fill=COLORS['accent_deep_purple'],
                                font=('Arial', 11, 'bold'))

    def animate_message_on_bus(self, source_x, dest_stations, data, msg_type, is_station_to_station=False,
                               message=None):

        if msg_type == "station_broadcast":
            message_color = COLORS['station_broadcast_color']
            message_symbol = ""
        elif is_station_to_station:
            message_color = COLORS['station_to_station_color']
            message_symbol = ""
        elif msg_type == "broadcast":
            message_color = COLORS['accent_rose']
            message_symbol = ""
        else:
            message_color = COLORS['accent_mint']
            message_symbol = ""

        message_circle = self.canvas.create_oval(
            source_x - 15, 115, source_x + 15, 135,
            fill=message_color, outline=COLORS['text_dark'], width=1
        )

        message_text = self.canvas.create_text(
            source_x, 125,
            text=message_symbol,
            fill='white',
            font=('Arial', 10)
        )

        if msg_type in ["broadcast", "station_broadcast"]:
            target_x = 750
        else:
            target_station = dest_stations[0] if dest_stations else None
            target_x = target_station.x if target_station else 750

        current_x = source_x
        step = 5

        while current_x < target_x:
            current_x += step
            self.canvas.coords(message_circle, current_x - 15, 115, current_x + 15, 135)
            self.canvas.coords(message_text, current_x, 125)
            self.canvas.update()
            time.sleep(0.02)

        time.sleep(0.3)
        self.canvas.delete(message_circle)
        self.canvas.delete(message_text)

    def send_message(self, source_addr, dest_addr, data, msg_type="unicast", source_x=None):
        message = Message(source_addr, dest_addr, data, msg_type)

        print(f" Отправка пакета: {message.get_packet_info()}")

        with self.lock:
            recipients = []
            dest_stations = []

            if msg_type == "broadcast" or dest_addr == 0xFF:
                for station in self.stations:
                    if station.receive_message(message):
                        recipients.append(station.name)
                        dest_stations.append(station)
            elif msg_type == "station_broadcast" or dest_addr == 0xFE:
                for station in self.stations:
                    if station.address != source_addr:
                        if station.receive_message(message):
                            recipients.append(station.name)
                            dest_stations.append(station)
            else:
                for station in self.stations:
                    if station.address == dest_addr:
                        if station.receive_message(message):
                            recipients.append(station.name)
                            dest_stations.append(station)
                        break

            if source_x is None:
                if source_addr == 0x00 and self.controller:
                    source_x = self.controller.x
                else:
                    for station in self.stations:
                        if station.address == source_addr:
                            source_x = station.x
                            break

            if source_x:
                is_station_to_station = source_addr != 0x00
                threading.Thread(
                    target=self.animate_message_on_bus,
                    args=(source_x, dest_stations, data, msg_type, is_station_to_station, message),
                    daemon=True
                ).start()

            return recipients


class NetworkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №5 - Схемы адресации с CRC8 проверкой")
        self.root.geometry("1000x800")
        self.root.configure(bg=COLORS['bg_primary'])

        self.setup_styles()

        self.canvas = tk.Canvas(self.root, width=800, height=250, bg=COLORS['bg_secondary'],
                                highlightthickness=2, highlightbackground=COLORS['accent_light_purple'],
                                relief='ridge')
        self.canvas.pack(pady=15, padx=20)

        self.network = Network(self.canvas, self)

        self.controller = NetworkController(self.network, self.canvas, 50, 80)
        self.network.set_controller(self.controller)

        self.create_stations()

        self.create_interface()

        self.update_thread = threading.Thread(target=self.update_interface, daemon=True)
        self.update_thread.start()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TFrame', background=COLORS['bg_primary'])
        self.style.configure('TLabel', background=COLORS['bg_primary'], foreground=COLORS['text_dark'],
                             font=('Arial', 9))
        self.style.configure('TLabelframe', background=COLORS['bg_light'], foreground=COLORS['accent_deep_purple'],
                             borderwidth=2, relief='ridge', font=('Arial', 10, 'bold'))
        self.style.configure('TLabelframe.Label', background=COLORS['bg_light'],
                             foreground=COLORS['accent_deep_purple'], font=('Arial', 10, 'bold'))

        self.style.configure('Primary.TButton',
                             background=COLORS['accent_purple'],
                             foreground='white',
                             borderwidth=1,
                             focuscolor='none',
                             font=('Arial', 9, 'bold'))
        self.style.map('Primary.TButton',
                       background=[('active', COLORS['accent_deep_purple']),
                                   ('pressed', COLORS['accent_violet'])])

        self.style.configure('Success.TButton',
                             background=COLORS['accent_mint'],
                             foreground=COLORS['text_dark'],
                             borderwidth=1,
                             font=('Arial', 9, 'bold'))
        self.style.map('Success.TButton',
                       background=[('active', '#8CFFE0'),
                                   ('pressed', '#70E6C4')])

        self.style.configure('Warning.TButton',
                             background=COLORS['accent_light_purple'],
                             foreground=COLORS['text_dark'],
                             borderwidth=1,
                             font=('Arial', 9, 'bold'))
        self.style.map('Warning.TButton',
                       background=[('active', COLORS['accent_purple']),
                                   ('pressed', COLORS['accent_deep_purple'])])

        self.style.configure('Broadcast.TButton',
                             background=COLORS['station_broadcast_color'],
                             foreground='white',
                             borderwidth=1,
                             font=('Arial', 9, 'bold'))
        self.style.map('Broadcast.TButton',
                       background=[('active', '#FF8C00'),
                                   ('pressed', '#E67C00')])

        self.style.configure('TEntry', fieldbackground=COLORS['bg_secondary'],
                             foreground=COLORS['text_dark'], borderwidth=1)

        self.style.configure('TCombobox', fieldbackground=COLORS['bg_secondary'],
                             foreground=COLORS['text_dark'], background=COLORS['bg_secondary'])

    def create_stations(self):
        stations_data = [
            (0x01, "Станция 1", 150, 170),
            (0x02, "Станция 2", 250, 170),
            (0x03, "Станция 3", 350, 170),
            (0x04, "Станция 4", 450, 170),
            (0x05, "Станция 5", 550, 170),
            (0x06, "Станция 6", 650, 170)
        ]

        for addr, name, x, y in stations_data:
            station = Station(addr, name, self.network, self.canvas, x, y)
            self.network.add_station(station)

    def create_interface(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text=" Управление передачей сообщений", padding="15")
        control_frame.pack(fill=tk.X, pady=8)

        control_row1 = ttk.Frame(control_frame)
        control_row1.pack(fill=tk.X, pady=10)

        ttk.Label(control_row1, text=" Адрес отправителя:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT,
                                                                                             padx=(0, 10))
        self.source_addr_entry = ttk.Entry(control_row1, width=12, font=('Arial', 10))
        self.source_addr_entry.pack(side=tk.LEFT, padx=(0, 25))
        self.source_addr_entry.insert(0, "0x01")

        ttk.Label(control_row1, text=" Адрес получателя:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.dest_addr_entry = ttk.Entry(control_row1, width=12, font=('Arial', 10))
        self.dest_addr_entry.pack(side=tk.LEFT, padx=(0, 25))
        self.dest_addr_entry.insert(0, "0x02")

        ttk.Label(control_row1, text=" Текст сообщения:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.message_entry = ttk.Entry(control_row1, width=40, font=('Arial', 10))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 25))
        self.message_entry.insert(0, "Тестовое сообщение")

        control_row2 = ttk.Frame(control_frame)
        control_row2.pack(fill=tk.X, pady=10)

        self.unicast_btn = ttk.Button(control_row2, text=" Unicast отправка",
                                      command=self.send_unicast, style='Primary.TButton', width=16)
        self.unicast_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.broadcast_btn = ttk.Button(control_row2, text=" Broadcast (от контроллера)",
                                        command=self.send_broadcast, style='Success.TButton', width=22)
        self.broadcast_btn.pack(side=tk.LEFT, padx=10)

        self.station_broadcast_btn = ttk.Button(control_row2, text=" Broadcast (от станции)",
                                                command=self.send_station_broadcast, style='Broadcast.TButton',
                                                width=20)
        self.station_broadcast_btn.pack(side=tk.LEFT, padx=10)

        self.clear_btn = ttk.Button(control_row2, text=" Очистить логи",
                                    command=self.clear_logs, style='Warning.TButton', width=14)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        info_frame = ttk.LabelFrame(main_frame, text="🖥 Информация о сети", padding="12")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        notebook = ttk.Notebook(info_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        stations_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stations_frame, text="Таблица станций")

        stations_text = tk.Text(stations_frame,
                                width=80,
                                height=12,
                                bg=COLORS['bg_secondary'],
                                fg=COLORS['text_dark'],
                                font=('Consolas', 10),
                                wrap=tk.WORD,
                                relief='solid',
                                borderwidth=2,
                                padx=10,
                                pady=10)
        stations_text.pack(fill=tk.BOTH, expand=True)

        stations_info = " КОНТРОЛЛЕР:\n"
        stations_info += "   Адрес: 0x00\n"
        stations_info += "   Описание: Центральный управляющий узел\n\n"

        stations_info += " СТАНЦИИ:\n"
        for station in self.network.stations:
            stations_info += f"   {station.name}: адрес {format_hex_address(station.address)}\n"

        stations_info += "\n СПЕЦИАЛЬНЫЕ АДРЕСА:\n"
        stations_info += "   0xFF - Broadcast от контроллера (всем станциям)\n"
        stations_info += "   0xFE - Broadcast от станции (всем ОСТАЛЬНЫМ станциям)\n"

        stations_info += "\n ИНСТРУКЦИЯ:\n"
        stations_info += "   1. Введите адрес отправителя (0x00-0x06)\n"
        stations_info += "   2. Введите адрес получателя:\n"
        stations_info += "      - 0x01-0x06 для unicast\n"
        stations_info += "      - 0xFF для broadcast от контроллера\n"
        stations_info += "      - 0xFE для broadcast от станции\n"
        stations_info += "   3. Введите текст сообщения\n"
        stations_info += "   4. Выберите тип отправки"

        stations_text.insert(1.0, stations_info)
        stations_text.config(state=tk.DISABLED)

        messages_frame = ttk.Frame(notebook, padding="10")
        notebook.add(messages_frame, text=" История сообщений")

        messages_container = ttk.Frame(messages_frame)
        messages_container.pack(fill=tk.BOTH, expand=True)

        self.messages_text = tk.Text(messages_container,
                                     width=80,
                                     height=15,
                                     bg=COLORS['bg_secondary'],
                                     fg=COLORS['text_dark'],
                                     font=('Consolas', 9),
                                     wrap=tk.WORD,
                                     relief='solid',
                                     borderwidth=2,
                                     padx=8,
                                     pady=8,
                                     highlightthickness=1,
                                     highlightbackground=COLORS['accent_light_purple'])
        self.messages_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        messages_scrollbar = ttk.Scrollbar(messages_container, orient=tk.VERTICAL, command=self.messages_text.yview)
        messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.messages_text.configure(yscrollcommand=messages_scrollbar.set)

        status_frame = ttk.Frame(main_frame, relief='solid', borderwidth=2)
        status_frame.pack(fill=tk.X, pady=(15, 0))

        self.status_label = ttk.Label(status_frame,
                                      text="Система готова. Введите адреса отправителя и получателя для отправки сообщения.",
                                      foreground=COLORS['accent_deep_purple'],
                                      font=('Arial', 10, 'bold'),
                                      background=COLORS['accent_lavender'],
                                      padding=(15, 8))
        self.status_label.pack(fill=tk.X)
        self.message_entry.focus()

    def update_interface(self):
        while True:
            time.sleep(0.5)
            messages_text = "=== ИСТОРИЯ СООБЩЕНИЙ ===\n\n"

            all_messages = []
            for station in self.network.stations:
                for msg in station.received_messages:
                    all_messages.append((msg.timestamp, station, msg))

            all_messages.sort(key=lambda x: x[0])

            for timestamp, station, msg in all_messages[-20:]:
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                source_name = "Контроллер" if msg.source_address == 0x00 else f"Станция 0x{msg.source_address:02X}"

                if msg.type == "station_broadcast":
                    msg_type_text = " [STATION BROADCAST]"
                elif msg.type == "broadcast":
                    msg_type_text = " [BROADCAST]"
                else:
                    msg_type_text = " [UNICAST]"

                messages_text += f" [{time_str}]{msg_type_text}\n"
                messages_text += f"    {source_name} → {station.name}\n"
                messages_text += f"    Данные: {msg.data}\n"
                messages_text += f"    CRC8: 0x{msg.checksum:02X} ✓\n\n"

            if not all_messages:
                messages_text = "Сообщений пока нет...\n\nОтправьте сообщение используя панель управления выше."

            self.root.after(0, self._update_messages_text, messages_text)

    def _update_messages_text(self, text):
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.insert(1.0, text)

    def clear_logs(self):
        for station in self.network.stations:
            station.received_messages.clear()
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.insert(1.0, "Логи очищены!")
        self.status_label.config(text="Все логи сообщений очищены", foreground=COLORS['accent_violet'])
        print("Логи сообщений очищены")

    def send_unicast(self):
        try:
            source_addr_text = self.source_addr_entry.get().strip()
            dest_addr_text = self.dest_addr_entry.get().strip()
            message_text = self.message_entry.get().strip()

            if not message_text:
                messagebox.showwarning("Внимание", "Пожалуйста, введите текст сообщения")
                return

            if not source_addr_text.startswith('0x'):
                source_addr_text = '0x' + source_addr_text
            if not dest_addr_text.startswith('0x'):
                dest_addr_text = '0x' + dest_addr_text

            source_addr = int(source_addr_text, 16)
            dest_addr = int(dest_addr_text, 16)

            valid_addresses = [0x00] + [station.address for station in self.network.stations]
            if source_addr not in valid_addresses:
                messagebox.showwarning("Ошибка отправителя",
                                       f"Отправитель с адресом {format_hex_address(source_addr)} не найден\n"
                                       f"Доступные адреса: {', '.join(format_hex_address(addr) for addr in valid_addresses)}")
                return

            if dest_addr in [0xFF, 0xFE]:
                if dest_addr == 0xFF:
                    messagebox.showwarning("Информация",
                                           "Для broadcast от контроллера используйте кнопку 'Broadcast (от контроллера)'")
                else:
                    messagebox.showwarning("Информация",
                                           "Для broadcast от станции используйте кнопку 'Broadcast (от станции)'")
                return

            if dest_addr not in valid_addresses:
                messagebox.showwarning("Ошибка получателя",
                                       f"Получатель с адресом {format_hex_address(dest_addr)} не найден\n"
                                       f"Доступные адреса: {', '.join(format_hex_address(addr) for addr in valid_addresses if addr != 0x00)}")
                return

            if source_addr == 0x00:
                recipients = self.controller.send_message(dest_addr, message_text, "unicast")
                sender_name = "Контроллер"
            else:
                source_station = None
                for station in self.network.stations:
                    if station.address == source_addr:
                        source_station = station
                        break
                if not source_station:
                    messagebox.showerror(" Ошибка",
                                         f"Не удалось найти станцию с адресом {format_hex_address(source_addr)}")
                    return
                recipients = source_station.send_message(dest_addr, message_text, "unicast")
                sender_name = source_station.name

            if recipients:
                dest_station = recipients[0]
                status_text = f" {sender_name} → {dest_station}: Unicast доставлен (CRC8 проверка пройдена)"
                self.status_label.config(text=status_text, foreground=COLORS['accent_deep_purple'])
            else:
                status_text = f" {sender_name} → {format_hex_address(dest_addr)}: Ошибка доставки"
                self.status_label.config(text=status_text, foreground=COLORS['accent_rose'])

        except ValueError:
            messagebox.showerror(" Ошибка", "Неверный формат адреса. Используйте hex-формат (0x00, 0x01, 0x02, ...)")

    def send_broadcast(self):
        try:
            source_addr_text = self.source_addr_entry.get().strip()
            message_text = self.message_entry.get().strip()

            if not message_text:
                messagebox.showwarning("Внимание", "Пожалуйста, введите текст сообщения")
                return

            if not source_addr_text.startswith('0x'):
                source_addr_text = '0x' + source_addr_text

            source_addr = int(source_addr_text, 16)

            valid_addresses = [0x00] + [station.address for station in self.network.stations]
            if source_addr not in valid_addresses:
                messagebox.showwarning("Ошибка отправителя",
                                       f"Отправитель с адресом {format_hex_address(source_addr)} не найден\n"
                                       f"Доступные адреса: {', '.join(format_hex_address(addr) for addr in valid_addresses)}")
                return

            if source_addr != 0x00:
                messagebox.showwarning("Предупреждение",
                                       "Для broadcast от контроллера установите адрес отправителя 0x00\n"
                                       "Для broadcast от станции используйте кнопку 'Broadcast (от станции)'")
                self.source_addr_entry.delete(0, tk.END)
                self.source_addr_entry.insert(0, "0x00")
                return

            self.dest_addr_entry.delete(0, tk.END)
            self.dest_addr_entry.insert(0, "0xFF")

            recipients = self.controller.send_message(0xFF, message_text, "broadcast")
            sender_name = "Контроллер"

            if recipients:
                status_text = f" {sender_name} → Все станции: Broadcast доставлен {len(recipients)} станциям (CRC8 проверка пройдена)"
                self.status_label.config(text=status_text, foreground=COLORS['accent_mint'])
            else:
                status_text = f" {sender_name} → Все станции: Ошибка доставки"
                self.status_label.config(text=status_text, foreground=COLORS['accent_rose'])

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат адреса. Используйте hex-формат (0x00, 0x01, 0x02, ...)")

    def send_station_broadcast(self):
        try:
            source_addr_text = self.source_addr_entry.get().strip()
            message_text = self.message_entry.get().strip()

            if not message_text:
                messagebox.showwarning("Внимание", "Пожалуйста, введите текст сообщения")
                return

            if not source_addr_text.startswith('0x'):
                source_addr_text = '0x' + source_addr_text

            source_addr = int(source_addr_text, 16)

            valid_addresses = [0x00] + [station.address for station in self.network.stations]
            if source_addr not in valid_addresses:
                messagebox.showwarning("Ошибка отправителя",
                                       f"Отправитель с адресом {format_hex_address(source_addr)} не найден\n"
                                       f"Доступные адреса: {', '.join(format_hex_address(addr) for addr in valid_addresses)}")
                return

            if source_addr == 0x00:
                messagebox.showwarning("Информация",
                                       "Для broadcast от станции выберите адрес станции (0x01-0x06) в поле отправителя\n"
                                       "Для broadcast от контроллера используйте кнопку 'Broadcast (от контроллера)'")
                return

            self.dest_addr_entry.delete(0, tk.END)
            self.dest_addr_entry.insert(0, "0xFE")

            source_station = None
            for station in self.network.stations:
                if station.address == source_addr:
                    source_station = station
                    break

            if not source_station:
                messagebox.showerror(" Ошибка",
                                     f"Не удалось найти станцию с адресом {format_hex_address(source_addr)}")
                return

            recipients = source_station.send_message(0xFE, message_text, "station_broadcast")
            sender_name = source_station.name

            if recipients:
                status_text = f" {sender_name} → Все остальные станции: Broadcast доставлен {len(recipients)} станциям (CRC8 проверка пройдена)"
                self.status_label.config(text=status_text, foreground=COLORS['station_broadcast_color'])
            else:
                status_text = f" {sender_name} → Все остальные станции: Ошибка доставки"
                self.status_label.config(text=status_text, foreground=COLORS['accent_rose'])

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат адреса. Используйте hex-формат (0x00, 0x01, 0x02, ...)")

    def on_closing(self):
        for station in self.network.stations:
            station.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = NetworkApp(root)

    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()