import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
from datetime import datetime
import threading

class SerialSender:
    def __init__(self, root):
        self.root = root
        self.root.title("🌺 Serial Sender - COM4")
        self.root.geometry("900x500")
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
        self.last_text = ""

        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.white, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        header_frame = tk.Frame(main_frame, bg=self.white)
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(header_frame, text="🌺 Serial Data Sender",
                               font=("Segoe UI", 18, "bold"),
                               fg=self.dark_purple, bg=self.white)
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(header_frame, text="Отправка данных через последовательный порт",
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

        input_frame = tk.Frame(main_frame, bg=self.white)
        input_frame.pack(fill="x", pady=(0, 15))

        input_header = tk.Frame(input_frame, bg=self.white)
        input_header.pack(fill="x", pady=(0, 8))

        tk.Label(input_header, text="✏️ Ввод текста",
                 font=("Segoe UI", 12, "bold"),
                 fg=self.dark_purple, bg=self.white).pack(side="left")

        info_label = tk.Label(input_header, text="Текст отправляется автоматически при вводе",
                              font=("Segoe UI", 9),
                              fg="#666666", bg=self.white)
        info_label.pack(side="right")

        self.data_entry = tk.Entry(input_frame, font=("Segoe UI", 11),
                                   bg=self.white, fg=self.text_color,
                                   relief="solid", borderwidth=1,
                                   highlightcolor=self.purple,
                                   highlightthickness=1)
        self.data_entry.pack(fill="x", pady=(0, 5))
        self.data_entry.insert(0, "Введите текст здесь...")
        self.data_entry.config(state="disabled")
        self.data_entry.bind("<KeyRelease>", self.on_text_change)

        log_frame = tk.Frame(main_frame, bg=self.white)
        log_frame.pack(fill="both", expand=True)

        log_header = tk.Frame(log_frame, bg=self.white)
        log_header.pack(fill="x", pady=(0, 8))

        tk.Label(log_header, text="📋 Лог отправки",
                 font=("Segoe UI", 12, "bold"),
                 fg=self.dark_purple, bg=self.white).pack(side="left")

        self.bytes_label = tk.Label(log_header, text="Отправлено байт: 0",
                                    font=("Segoe UI", 9),
                                    fg="#666666", bg=self.white)
        self.bytes_label.pack(side="right")

        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  font=("Consolas", 9),
                                                  wrap="word",
                                                  bg=self.white,
                                                  fg=self.text_color,
                                                  relief="flat",
                                                  borderwidth=1,
                                                  padx=10, pady=10)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")

        tools_frame = tk.Frame(log_frame, bg=self.white)
        tools_frame.pack(fill="x", pady=(10, 0))

        self.clear_btn = tk.Button(tools_frame, text="🧹 Очистить лог",
                                   command=self.clear_log,
                                   bg=self.lavender, fg=self.dark_purple,
                                   font=("Segoe UI", 9), relief="flat",
                                   padx=12, pady=4)
        self.clear_btn.pack(side="right")

        self.bytes_sent = 0

    def refresh_ports(self):
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [f"{port.device} - {port.description}" for port in ports]
            self.port_combo['values'] = port_list
            if port_list:
                self.port_combo.set(port_list[0])
        except Exception as e:
            self.log(f"❌ Ошибка поиска портов: {str(e)}")

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
                self.update_status(True)
                self.data_entry.config(state="normal")
                self.data_entry.select_range(0, tk.END)
                self.data_entry.focus()
                self.log(f"✅ Подключено к {port_name}, скорость: {baud_rate} бод")
                self.log("💫 Вводите текст - он будет отправляться автоматически")

        except Exception as e:
            self.log(f"❌ Ошибка подключения: {str(e)}")

    def disconnect(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connected = False
        self.update_status(False)
        self.data_entry.config(state="disabled")
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

    def on_text_change(self, event):
        if not self.connected or not self.serial_port or not self.serial_port.is_open:
            return

        current_text = self.data_entry.get()

        if current_text and current_text != self.last_text:
            self.send_data(current_text)
            self.last_text = current_text

    def send_data(self, data):
        try:
            data_to_send = data + '\n'
            bytes_sent = self.serial_port.write(data_to_send.encode('utf-8'))

            if bytes_sent > 0:
                self.bytes_sent += bytes_sent
                self.log(f"✉️ Отправлено: '{data.strip()}' ({bytes_sent} байт)")
                self.bytes_label.config(text=f"Отправлено байт: {self.bytes_sent}")

        except Exception as e:
            self.log(f"❌ Ошибка отправки: {str(e)}")
            self.disconnect()

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        self.bytes_sent = 0
        self.bytes_label.config(text="Отправлено байт: 0")
        self.log("🧹 Лог очищен")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"

        self.log_text.config(state="normal")
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

def main():
    root = tk.Tk()
    app = SerialSender(root)
    root.mainloop()

if __name__ == "__main__":
    main()