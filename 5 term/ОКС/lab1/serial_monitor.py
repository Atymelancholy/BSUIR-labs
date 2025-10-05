import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
from datetime import datetime
import threading

class SerialReceiver:
    def __init__(self, root):
        self.root = root
        self.root.title("🌸 Serial Receiver - COM3")
        self.root.geometry("900x600")
        self.root.configure(bg='white')

        self.lavender = "#e6e6fa"
        self.light_lavender = "#f5f5ff"
        self.purple = "#9370db"
        self.dark_purple = "#6a5acd"
        self.white = "#ffffff"
        self.gray = "#f8f9fa"
        self.text_color = "#4a4a4a"

        self.serial_port = None
        self.connected = False
        self.receiving = False

        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.white, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        header_frame = tk.Frame(main_frame, bg=self.white)
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(header_frame, text="🌸 Serial Data Receiver",
                               font=("Segoe UI", 18, "bold"),
                               fg=self.dark_purple, bg=self.white)
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(header_frame, text="Монитор последовательного порта",
                                  font=("Segoe UI", 11),
                                  fg="#888888", bg=self.white)
        subtitle_label.pack(anchor="w", pady=(5, 0))

        control_frame = tk.Frame(main_frame, bg=self.light_lavender,
                                 relief="flat", bd=0, padx=15, pady=15)
        control_frame.pack(fill="x", pady=(0, 20))

        settings_frame = tk.Frame(control_frame, bg=self.light_lavender)
        settings_frame.pack(fill="x", pady=(0, 10))

        tk.Label(settings_frame, text="COM Port:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.dark_purple, bg=self.light_lavender).pack(side="left", padx=(0, 10))

        self.port_combo = ttk.Combobox(settings_frame, state="readonly",
                                       width=20, font=("Segoe UI", 9))
        self.port_combo.pack(side="left", padx=(0, 20))

        self.refresh_btn = tk.Button(settings_frame, text="🔄 Обновить",
                                     command=self.refresh_ports,
                                     bg=self.purple, fg=self.white,
                                     font=("Segoe UI", 9), relief="flat",
                                     padx=10, pady=2)
        self.refresh_btn.pack(side="left", padx=(0, 20))

        tk.Label(settings_frame, text="Baud Rate:",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.dark_purple, bg=self.light_lavender).pack(side="left", padx=(0, 10))

        self.baud_combo = ttk.Combobox(settings_frame,
                                       values=[9600, 19200, 38400, 57600, 115200],
                                       state="readonly", width=10, font=("Segoe UI", 9))
        self.baud_combo.set(9600)
        self.baud_combo.pack(side="left")

        self.connect_button = tk.Button(control_frame, text="Подключиться",
                                        bg=self.purple, fg=self.white,
                                        font=("Segoe UI", 10, "bold"),
                                        command=self.toggle_connection,
                                        relief="flat", padx=20, pady=8)
        self.connect_button.pack(pady=(5, 0))

        status_frame = tk.Frame(control_frame, bg=self.light_lavender)
        status_frame.pack(fill="x", pady=(10, 0))

        self.status_canvas = tk.Canvas(status_frame, width=16, height=16,
                                       bg="red", highlightthickness=0, bd=0)
        self.status_canvas.create_oval(2, 2, 14, 14, fill="red")
        self.status_canvas.pack(side="left")

        self.status_label = tk.Label(status_frame, text="Отключено",
                                     font=("Segoe UI", 9, "bold"),
                                     fg="red", bg=self.light_lavender)
        self.status_label.pack(side="left", padx=8)

        data_frame = tk.Frame(main_frame, bg=self.white)
        data_frame.pack(fill="both", expand=True)

        data_header = tk.Frame(data_frame, bg=self.white)
        data_header.pack(fill="x", pady=(0, 10))

        tk.Label(data_header, text="📨 Полученные данные",
                 font=("Segoe UI", 12, "bold"),
                 fg=self.dark_purple, bg=self.white).pack(side="left")

        self.bytes_label = tk.Label(data_header, text="Получено байт: 0",
                                    font=("Segoe UI", 9),
                                    fg="#666666", bg=self.white)
        self.bytes_label.pack(side="right")

        self.data_text = scrolledtext.ScrolledText(data_frame,
                                                   font=("Consolas", 10),
                                                   wrap="word",
                                                   bg=self.white,
                                                   fg=self.text_color,
                                                   relief="flat",
                                                   borderwidth=1,
                                                   padx=10, pady=10)
        self.data_text.pack(fill="both", expand=True)
        self.data_text.config(state="disabled")

        tools_frame = tk.Frame(data_frame, bg=self.white)
        tools_frame.pack(fill="x", pady=(10, 0))

        self.clear_btn = tk.Button(tools_frame, text="🧹 Очистить",
                                   command=self.clear_data,
                                   bg=self.lavender, fg=self.dark_purple,
                                   font=("Segoe UI", 9), relief="flat",
                                   padx=12, pady=4)
        self.clear_btn.pack(side="right")

        self.bytes_received = 0

    def refresh_ports(self):
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [f"{port.device} - {port.description}" for port in ports]
            self.port_combo['values'] = port_list
            if port_list:
                self.port_combo.set(port_list[0])
        except Exception as e:
            self.log(f"Ошибка поиска портов: {str(e)}")

    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        try:
            port_selection = self.port_combo.get()
            if not port_selection:
                self.log("Выберите COM порт!")
                return

            port_name = port_selection.split(" - ")[0]
            baud_rate = int(self.baud_combo.get())

            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=8,
                stopbits=1,
                parity='N',
                timeout=0.1
            )

            if self.serial_port.is_open:
                self.connected = True
                self.receiving = True
                self.update_status(True)
                self.log(f"✅ Подключено к {port_name}, скорость: {baud_rate} бод")
                self.start_receiving()

        except Exception as e:
            self.log(f"❌ Ошибка подключения: {str(e)}")

    def disconnect(self):
        self.receiving = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connected = False
        self.update_status(False)
        self.log("🔌 Отключено")

    def update_status(self, connected):
        if connected:
            self.connect_button.config(text="Отключиться", bg="#d8bfd8")
            self.status_canvas.config(bg="green")
            self.status_canvas.delete("all")
            self.status_canvas.create_oval(2, 2, 14, 14, fill="green")
            self.status_label.config(text="Подключено", fg="green")
        else:
            self.connect_button.config(text="Подключиться", bg=self.purple)
            self.status_canvas.config(bg="red")
            self.status_canvas.delete("all")
            self.status_canvas.create_oval(2, 2, 14, 14, fill="red")
            self.status_label.config(text="Отключено", fg="red")

    def start_receiving(self):
        def receive_loop():
            while self.receiving and self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        if data:
                            self.display_data(data)
                except Exception as e:
                    self.log(f"❌ Ошибка чтения: {str(e)}")
                    break

        self.receive_thread = threading.Thread(target=receive_loop, daemon=True)
        self.receive_thread.start()

    def display_data(self, data):
        text = data.decode('utf-8', errors='replace')
        self.bytes_received += len(data)

        self.data_text.config(state="normal")
        self.data_text.insert("end", text)
        self.data_text.see("end")
        self.data_text.config(state="disabled")

        self.bytes_label.config(text=f"Получено байт: {self.bytes_received}")

    def clear_data(self):
        self.data_text.config(state="normal")
        self.data_text.delete(1.0, "end")
        self.data_text.config(state="disabled")
        self.bytes_received = 0
        self.bytes_label.config(text="Получено байт: 0")
        self.log("🧹 Данные очищены")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

def main():
    root = tk.Tk()
    app = SerialReceiver(root)
    root.mainloop()

if __name__ == "__main__":
    main()