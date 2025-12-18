import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import socket

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False

FLAG = 0x7E
ESC = 0x7D
ESC_XOR = 0x20

COLORS = {
    "field_bg": "#ffffff",
    "flag": "#cfe9ff",
    "length": "#ffd7a6",
    "data": "#d8f8d8",
    "checksum": "#f7d1d1",
    "ok": "#bff0bf",
    "highlight": "#9ee7ff",
    "error": "#ff9090",
    "correct": "#90ff90",
    "border": "#777777"
}

CRC_POLYNOMIALS = {
    "CRC-8": 0x07,
    "CRC-16-CCITT": 0x1021,
    "CRC-16": 0x8005
}

def bytes_to_hex(bts: bytes) -> str:
    return ' '.join(f"{x:02X}" for x in bts)

def stuff_bytes(raw: bytes) -> bytes:
    out = bytearray()
    for b in raw:
        if b == FLAG or b == ESC:
            out.append(ESC)
            out.append(b ^ ESC_XOR)
        else:
            out.append(b)
    return bytes(out)

def unstuff_bytes(stuffed: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(stuffed):
        b = stuffed[i]
        if b == ESC:
            i += 1
            if i >= len(stuffed):
                break
            out.append(stuffed[i] ^ ESC_XOR)
        else:
            out.append(b)
        i += 1
    return bytes(out)

def binary_subtraction(a: str, b: str) -> str:
    result = []
    borrow = 0
    max_len = max(len(a), len(b))
    a = a.zfill(max_len)
    b = b.zfill(max_len)

    for i in range(max_len-1, -1, -1):
        bit_a = int(a[i])
        bit_b = int(b[i])

        if bit_a - borrow >= bit_b:
            result.append(str(bit_a - borrow - bit_b))
            borrow = 0
        else:
            result.append(str(2 + bit_a - borrow - bit_b))
            borrow = 1

    return ''.join(result[::-1]).lstrip('0')

def compute_crc_division_verification(data: bytes, received_crc: int, polynomial: int, crc_type: str) -> tuple:
    steps = []
    division_steps = []

    if crc_type == "CRC-8":
        crc_bits = 8
        poly_degree = 8
    else:  # CRC-16
        crc_bits = 16
        poly_degree = 16

    data_bits = ''
    for byte in data:
        data_bits += format(byte, '08b')

    crc_bits_str = format(received_crc, f'0{crc_bits}b')

    dividend = data_bits + crc_bits_str
    poly_bits = format(polynomial, f'0{crc_bits+1}b')

    steps.append(f"=== ВЕРИФИКАЦИЯ CRC-{crc_bits} МЕТОДОМ ДЕЛЕНИЯ ===")
    steps.append(f"Данные: {bytes_to_hex(data)}")
    steps.append(f"Полученный CRC: 0x{received_crc:0{crc_bits//4}X}")
    steps.append(f"Данные + CRC: {dividend}")
    steps.append(f"Полином: {poly_bits}")
    steps.append("")

    current = dividend
    division_steps.append({
        'current': current,
        'operation': 'Начальное состояние',
        'poly': '',
        'result': current
    })

    for i in range(len(data_bits)):
        steps.append(f"Шаг {i+1}:")

        if current[0] == '1':
            steps.append(f"  Старший бит = 1 → выполняем вычитание полинома")

            current_part = current[:poly_degree+1]

            result_part = binary_subtraction(current_part, poly_bits)

            result_part = result_part.zfill(poly_degree+1)

            current = result_part + current[poly_degree+1:]

            division_steps.append({
                'current': dividend,
                'operation': f'Шаг {i+1}: Вычитание полинома',
                'poly': poly_bits + '0' * (len(current) - len(poly_bits)),
                'result': current
            })

            steps.append(f"  Вычитаем: {current_part} - {poly_bits} = {result_part}")
            steps.append(f"  Результат: {current}")
        else:
            steps.append(f"  Старший бит = 0 → сдвигаем")
            division_steps.append({
                'current': current,
                'operation': f'Шаг {i+1}: Сдвиг',
                'poly': '',
                'result': current[1:] + '0'
            })
            current = current[1:] + '0'
            steps.append(f"  После сдвига: {current}")

        steps.append("")

    remainder = current[:crc_bits]
    remainder_value = int(remainder, 2)

    steps.append(f"Остаток от деления: {remainder} = 0x{remainder_value:0{crc_bits//4}X}")

    if remainder_value == 0:
        steps.append("✅ ВЕРИФИКАЦИЯ УСПЕШНА!")
        steps.append("Остаток от деления равен 0 - CRC корректный!")
        verification_passed = True
    else:
        steps.append("❌ ВЕРИФИКАЦИЯ НЕ УДАЛАСЬ!")
        steps.append("Остаток от деления не равен 0 - CRC содержит ошибки!")
        verification_passed = False

    return verification_passed, steps, division_steps

def compute_crc(data: bytes, polynomial: int, crc_type: str) -> int:
    if crc_type == "CRC-8":
        crc_bits = 8
        poly_degree = 8
    else:  # CRC-16
        crc_bits = 16
        poly_degree = 16

    data_bits = ''
    for byte in data:
        data_bits += format(byte, '08b')

    dividend = data_bits + '0' * crc_bits
    poly_bits = format(polynomial, f'0{crc_bits+1}b')

    current = dividend
    for i in range(len(data_bits)):
        if current[0] == '1':
            current_part = current[:poly_degree+1]

            result_part = binary_subtraction(current_part, poly_bits)

            result_part = result_part.zfill(poly_degree+1)

            current = result_part + current[poly_degree+1:]
        else:
            current = current[1:] + '0'

    remainder = current[:crc_bits]
    return int(remainder, 2)

class ReceiverApp:
    def __init__(self, root):
        self.root = root
        root.title("Receiver — Variant 2 (Byte-stuffing + CRC Division)")
        root.geometry("1400x1000")
        self.last_frame = None
        self._recv_buf = bytearray()
        self.parse_steps = []
        self.parse_index = 0
        self.running = False
        self.serial_obj = None
        self.udp_thread = None
        self.serial_thread = None
        self.crc_verification_steps = []
        self.division_steps = []
        self.current_crc_step = 0

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")

        ctrl = ttk.Labelframe(top, text="Controls & CRC Settings", padding=8)
        ctrl.pack(side="left", fill="y", padx=(0,8))

        ttk.Label(ctrl, text="CRC Settings:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(0,4))

        ttk.Label(ctrl, text="CRC Type:").pack(anchor="w")
        self.crc_type = tk.StringVar(value="CRC-8")
        crc_combo = ttk.Combobox(ctrl, textvariable=self.crc_type,
                                 values=list(CRC_POLYNOMIALS.keys()), state="readonly", width=12)
        crc_combo.pack(fill="x")

        ttk.Label(ctrl, text="Polynomial:").pack(anchor="w", pady=(6,0))
        self.poly_var = tk.StringVar(value="0x07")
        self.poly_entry = ttk.Entry(ctrl, textvariable=self.poly_var, width=10)
        self.poly_entry.pack(fill="x")

        ttk.Separator(ctrl).pack(fill="x", pady=8)

        ttk.Label(ctrl, text="Mode:").pack(anchor="w")
        self.mode_var = tk.StringVar(value="udp" if not SERIAL_AVAILABLE else "serial")
        ttk.Radiobutton(ctrl, text="UDP (sim)", variable=self.mode_var, value="udp").pack(anchor="w")
        ttk.Radiobutton(ctrl, text="Serial (COM)", variable=self.mode_var, value="serial").pack(anchor="w")

        ttk.Label(ctrl, text="COM port:").pack(anchor="w", pady=(6,0))
        self.port_combo = ttk.Combobox(ctrl, state="readonly", width=18)
        self.port_combo['values'] = self._get_serial_ports()
        if self.port_combo['values']:
            self.port_combo.current(0)
        self.port_combo.pack(fill="x")

        self.connect_btn = ttk.Button(ctrl, text="Listen", command=self._toggle_listen)
        self.connect_btn.pack(fill="x", pady=(6,0))

        ttk.Label(ctrl, text="UDP port:").pack(anchor="w", pady=(8,0))
        self.udp_entry = ttk.Entry(ctrl)
        self.udp_entry.insert(0, "5006")
        self.udp_entry.pack(fill="x")

        ttk.Button(ctrl, text="Simulate incoming (paste hex)", command=self._open_simulate_dialog).pack(fill="x", pady=(10,6))
        ttk.Button(ctrl, text="Clear display", command=self._clear_display).pack(fill="x", pady=(0,6))

        ttk.Label(ctrl, text="Error injection (applies to last frame):").pack(anchor="w", pady=(8,0))
        eframe = ttk.Frame(ctrl)
        eframe.pack(fill="x", pady=(4,6))
        ttk.Button(eframe, text="Bad CRC", command=self._inject_bad_crc).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(eframe, text="Bad Length", command=self._inject_bad_length).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(eframe, text="Cut Data", command=self._inject_cut_data).pack(side="left", expand=True, fill="x", padx=2)

        ttk.Separator(ctrl).pack(fill="x", pady=6)
        ttk.Label(ctrl, text="Quick templates").pack(anchor="w")
        ttk.Button(ctrl, text="Correct example", command=self._paste_correct_example).pack(fill="x", pady=3)
        ttk.Button(ctrl, text="Bad CRC example", command=self._paste_badcrc_example).pack(fill="x", pady=3)
        ttk.Button(ctrl, text="Bad Len example", command=self._paste_badlen_example).pack(fill="x", pady=3)

        vis = ttk.Labelframe(top, text="Visualization & CRC Verification", padding=8)
        vis.pack(side="left", fill="both", expand=True)

        self.anim_canvas = tk.Canvas(vis, height=100, bg="#f7f7f7")
        self.anim_canvas.pack(fill="x", pady=(0,8))

        ttk.Label(vis, text="Raw received bytes (hex stream):").pack(anchor="w")
        self.raw_stream = scrolledtext.ScrolledText(vis, height=4)
        self.raw_stream.pack(fill="x", pady=(4,8))

        self.error_frame = ttk.Frame(vis)
        self.error_frame.pack(fill="x", pady=4)
        self.error_label = ttk.Label(self.error_frame, text="", foreground="red", font=("TkDefaultFont", 9, "bold"))
        self.error_label.pack()

        ttk.Label(vis, text="Packet layout (fields highlight step-by-step):").pack(anchor="w")
        self.packet_canvas = tk.Canvas(vis, height=140, bg="white")
        self.packet_canvas.pack(fill="x", pady=(6,8))
        self._create_packet_boxes()

        self.division_frame = ttk.LabelFrame(vis, text="CRC Verification Division", padding=8)
        self.division_frame.pack(fill="x", pady=4)

        self.division_canvas = tk.Canvas(self.division_frame, height=200, bg="white")
        self.division_canvas.pack(fill="x", pady=4)

        step_frame = ttk.Frame(self.division_frame)
        step_frame.pack(fill="x", pady=4)
        ttk.Button(step_frame, text="Show Verification Steps", command=self._show_verification_steps).pack(side="left", padx=2)
        ttk.Button(step_frame, text="Next Step", command=self._next_verification_step).pack(side="left", padx=2)
        ttk.Button(step_frame, text="Reset Steps", command=self._reset_verification_steps).pack(side="left", padx=2)

        self.steps_text = scrolledtext.ScrolledText(self.division_frame, height=4)
        self.steps_text.pack(fill="x")
        self.steps_text.insert("1.0", "Verification steps will be shown here...")
        self.steps_text.config(state="disabled")

        ttk.Label(vis, text="Step-by-step parsing:").pack(anchor="w")
        self.steps_frame = tk.Frame(vis)
        self.steps_frame.pack(fill="both", expand=True)

        ttk.Label(main, text="Log:").pack(anchor="w", pady=(8,0))
        self.log_text = scrolledtext.ScrolledText(main, height=8)
        self.log_text.pack(fill="both", expand=True)

        self._log("Receiver ready")

    def _show_verification_steps(self):
        if not hasattr(self, 'last_data'):
            return

        polynomial = int(self.poly_var.get(), 16)
        crc_type = self.crc_type.get()

        verification_passed, self.crc_verification_steps, self.division_steps = compute_crc_division_verification(
            self.last_data, self.last_received_crc, polynomial, crc_type)
        self.current_crc_step = 0

        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0", "end")
        self.steps_text.insert("1.0", "Click 'Next Step' to see verification steps...")
        self.steps_text.config(state="disabled")

        self._draw_verification_step(0)
        self._log(f"Verification steps prepared. Verification {'PASSED' if verification_passed else 'FAILED'}")

    def _draw_verification_step(self, step_index):
        self.division_canvas.delete("all")

        if not self.division_steps or step_index >= len(self.division_steps):
            return

        step = self.division_steps[step_index]
        w = self.division_canvas.winfo_width() or 800
        h = 180

        status = "✅ PASSED" if step_index == len(self.division_steps) - 1 and not self.last_crc_error else "❌ FAILED" if step_index == len(self.division_steps) - 1 else ""
        self.division_canvas.create_text(10, 10, anchor="nw", text=f"{step['operation']} {status}",
                                         font=("TkDefaultFont", 10, "bold"))

        y = 40
        line_height = 25

        self.division_canvas.create_text(10, y, anchor="nw", text="Текущее:", font=("TkDefaultFont", 9))
        self.division_canvas.create_text(80, y, anchor="nw", text=step['current'],
                                         font=("Courier", 9), fill="blue")
        y += line_height

        if step['poly']:
            self.division_canvas.create_text(10, y, anchor="nw", text="Вычитаем: ", font=("TkDefaultFont", 9))
            self.division_canvas.create_text(80, y, anchor="nw", text=step['poly'],
                                             font=("Courier", 9), fill="red")
            y += line_height

            line_y = y - 5
            self.division_canvas.create_line(80, line_y, 80 + len(step['current']) * 6, line_y, fill="gray")
            y += line_height

        self.division_canvas.create_text(10, y, anchor="nw", text="Результат:", font=("TkDefaultFont", 9))
        self.division_canvas.create_text(80, y, anchor="nw", text=step['result'],
                                         font=("Courier", 9), fill="green")

    def _next_verification_step(self):
        if not self.division_steps or self.current_crc_step >= len(self.division_steps):
            return

        self.steps_text.config(state="normal")
        if self.current_crc_step == 0:
            self.steps_text.delete("1.0", "end")

        if self.current_crc_step < len(self.crc_verification_steps):
            self.steps_text.insert("end", f"{self.crc_verification_steps[self.current_crc_step]}\n")
        self.steps_text.see("end")
        self.steps_text.config(state="disabled")

        self._draw_verification_step(self.current_crc_step)
        self.current_crc_step += 1

    def _reset_verification_steps(self):
        self.crc_verification_steps = []
        self.division_steps = []
        self.current_crc_step = 0
        self.division_canvas.delete("all")
        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0", "end")
        self.steps_text.insert("1.0", "Verification steps reset.")
        self.steps_text.config(state="disabled")

    def _get_serial_ports(self):
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def _toggle_listen(self):
        if self.running:
            self.running = False
            self.connect_btn.config(text="Listen")
            if self.serial_obj:
                try:
                    self.serial_obj.close()
                except:
                    pass
            self._log("Stopped listening")
            return

        mode = self.mode_var.get()
        if mode == "serial":
            if not SERIAL_AVAILABLE:
                return
            port = self.port_combo.get()
            if not port:
                return
            try:
                self.serial_obj = serial.Serial(port, 9600, timeout=0.2)
            except Exception as e:
                return
            self.running = True
            self.connect_btn.config(text="Stop")
            self._log(f"Serial listening on {port}")
            self.serial_thread = threading.Thread(target=self._serial_read_loop, daemon=True)
            self.serial_thread.start()
        else:
            try:
                port = int(self.udp_entry.get())
            except Exception:
                return
            self.running = True
            self.connect_btn.config(text="Stop")
            self._log(f"UDP listening on port {port}")
            self.udp_thread = threading.Thread(target=self._udp_listen_loop, args=(port,), daemon=True)
            self.udp_thread.start()

    def _serial_read_loop(self):
        while self.running and self.serial_obj and self.serial_obj.is_open:
            try:
                n = self.serial_obj.in_waiting
                if n > 0:
                    data = self.serial_obj.read(n)
                    self.root.after(1, lambda d=data: self._on_bytes_received(d))
            except Exception:
                break
        self._log("Serial loop ended")

    def _udp_listen_loop(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("0.0.0.0", port))
            sock.settimeout(0.5)
            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)
                    if data:
                        self._log(f"UDP packet from {addr}, {len(data)} bytes")
                        self.root.after(1, lambda d=data: self._on_bytes_received(d))
                except socket.timeout:
                    continue
                except Exception:
                    break
        finally:
            sock.close()
            self._log("UDP listener stopped")

    def _on_bytes_received(self, data: bytes):
        self.raw_stream.insert("end", bytes_to_hex(data) + " ")
        self.raw_stream.see("end")
        try:
            self._flash_incoming(data[-1])
        except Exception:
            pass
        self._recv_buf.extend(data)
        self._try_extract_frames()

    def _try_extract_frames(self):
        buf = self._recv_buf
        while True:
            if FLAG not in buf:
                break
            start = buf.index(FLAG)
            try:
                end = start + 1 + buf[start+1:].index(FLAG)
            except ValueError:
                if start > 0:
                    del buf[:start]
                break
            frame = bytes(buf[start:end+1])
            del buf[:end+1]
            self.last_frame = frame
            self.root.after(1, lambda f=frame: self._process_frame(f))

    def _process_frame(self, frame: bytes):
        self.error_label.config(text="")
        self._reset_verification_steps()

        for ch in self.steps_frame.winfo_children():
            ch.destroy()
        self._clear_packet_texts()
        self._reset_box_borders()

        self._log(f"Received frame: {bytes_to_hex(frame)}")

        if not (len(frame) >= 2 and frame[0] == FLAG and frame[-1] == FLAG):
            self._append_step("Error", "Missing start/end flag or too short", error=True)
            self._highlight_all_error()
            return

        self._set_box_text(0, f"{frame[0]:02X}")
        self._set_box_text(4, f"{frame[-1]:02X}")

        stuffed_mid = frame[1:-1]
        self._append_step("Between flags (stuffed)", stuffed_mid)

        unstuffed = unstuff_bytes(stuffed_mid)
        self._append_step("After unstuffing", unstuffed)

        crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1

        if len(unstuffed) < 1 + crc_size:
            self._append_step("Error", "Frame too short after unstuffing", error=True)
            self._highlight_all_error()
            return

        recv_len = unstuffed[0]
        data_end = len(unstuffed) - 1 - crc_size

        if data_end < 0:
            self._append_step("Error", "Invalid frame length", error=True)
            self._highlight_all_error()
            return

        data = unstuffed[1:1+data_end]
        recv_crc_bytes = unstuffed[1+data_end:1+data_end+crc_size]

        recv_crc = int.from_bytes(recv_crc_bytes, byteorder='big') if crc_size == 2 else recv_crc_bytes[0]

        polynomial = int(self.poly_var.get(), 16)
        correct_crc = compute_crc(data, polynomial, self.crc_type.get())

        self._set_box_text(1, f"{recv_len:02X}")
        self._set_box_text(2, bytes_to_hex(data) if data else "")

        crc_label = f"CRC-{crc_size*8}"
        self._set_box_text(3, f"{recv_crc:0{crc_size*2}X}")

        self.last_data = data
        self.last_received_crc = recv_crc
        self.last_crc_error = (correct_crc != recv_crc)

        self.parse_steps = []
        self.parse_steps.append((0, f"{frame[0]:02X}", False))

        len_text = f"{recv_len:02X}"
        if len(data) != recv_len:
            len_text = f"{recv_len:02X} (должно быть {len(data):02X})"
        self.parse_steps.append((1, len_text, len(data) != recv_len))

        if len(data) > 0:
            for i in range(len(data)):
                self.parse_steps.append((2, bytes_to_hex(data[:i+1]), False))
        else:
            self.parse_steps.append((2, "<empty>", False))

        crc_text = f"{recv_crc:0{crc_size*2}X}"
        if correct_crc != recv_crc:
            crc_text = f"{recv_crc:0{crc_size*2}X} (должно быть {correct_crc:0{crc_size*2}X})"
        self.parse_steps.append((3, crc_text, correct_crc != recv_crc))

        self.parse_steps.append((4, f"{frame[-1]:02X}", False))

        self.parse_index = 0
        self._animate_step()

    def _create_packet_boxes(self):
        self.packet_canvas.delete("all")
        w = self.packet_canvas.winfo_width() or 960
        h = 80
        gap = 8

        crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1
        crc_label = f"CRC-{crc_size*8}"

        labels = [("Flag", COLORS["flag"]), ("Len", COLORS["length"]), ("Data", COLORS["data"]),
                  (crc_label, COLORS["checksum"]), ("Flag", COLORS["flag"])]
        total = len(labels)
        boxw = max(110, (w - 20 - (total-1)*gap) // total)
        x = 10
        self._boxes = []
        for name, color in labels:
            rect = self.packet_canvas.create_rectangle(x, 20, x+boxw, 20+h, fill=color, outline=COLORS["border"], width=1)
            title = self.packet_canvas.create_text(x+6, 24, anchor="nw", text=name, font=("TkDefaultFont", 9, "bold"))
            content = self.packet_canvas.create_text(x+6, 44, anchor="nw", text="", width=boxw-12)
            self._boxes.append((rect, content))
            x += boxw + gap
        self.packet_canvas.bind("<Configure>", lambda e: self._create_packet_boxes())

    def _set_box_text(self, idx, text):
        if not hasattr(self, "_boxes"): return
        rect, content = self._boxes[idx]
        self.packet_canvas.itemconfigure(content, text=text)

    def _set_box_border(self, idx, color):
        rect, _ = self._boxes[idx]
        self.packet_canvas.itemconfigure(rect, outline=color, width=3)

    def _reset_box_borders(self):
        if not hasattr(self, "_boxes"): return
        for rect, _ in self._boxes:
            self.packet_canvas.itemconfigure(rect, outline=COLORS["border"], width=1)

    def _clear_packet_texts(self):
        if not hasattr(self, "_boxes"): return
        for rect, content in self._boxes:
            self.packet_canvas.itemconfigure(content, text="")
            self.packet_canvas.itemconfigure(rect, outline=COLORS["border"], width=1)

    def _append_step(self, title, data, error=False):
        f = ttk.Frame(self.steps_frame, relief="groove", borderwidth=1)
        f.pack(fill="x", pady=4)

        bg_color = COLORS["error"] if error else COLORS["data"]
        head = ttk.Label(f, text=title, background=bg_color)
        head.pack(fill="x")

        txt = tk.Text(f, height=3, wrap="word", borderwidth=0)
        if isinstance(data, (bytes, bytearray)):
            txt.insert("end", f"HEX: {bytes_to_hex(data)}\nASCII: {data.decode('utf-8', errors='replace')}")
        else:
            txt.insert("end", str(data))
        txt.config(state="disabled")
        txt.pack(fill="x")

    def _highlight_all_error(self):
        if not hasattr(self, "_boxes"): return
        for i in range(len(self._boxes)):
            self._set_box_border(i, COLORS["error"])

    def _animate_step(self):
        self._reset_box_borders()
        if self.parse_index >= len(self.parse_steps):
            return
        idx, text, is_error = self.parse_steps[self.parse_index]

        if is_error:
            self._set_box_border(idx, COLORS["error"])
            self._append_step(f"Step {self.parse_index+1} (ERROR)", text, error=True)
            self._log(f"Parsing error at field {idx}: {text}")
        else:
            self._set_box_border(idx, COLORS["highlight"])
            self._append_step(f"Step {self.parse_index+1}", text, error=False)

        self.parse_index += 1
        self.root.after(700, self._animate_step)

    def _flash_incoming(self, last_byte):
        self.anim_canvas.delete("all")
        w = self.anim_canvas.winfo_width() or 900
        x = w // 2
        y = 50
        r = 28
        oval = self.anim_canvas.create_oval(x-r, y-r, x+r, y+r, fill="#b6f5b6", outline="#4caf50")
        txt = self.anim_canvas.create_text(x, y, text=f"{last_byte:02X}", font=("TkDefaultFont", 12, "bold"))
        self.root.after(300, lambda: (self.anim_canvas.delete(oval), self.anim_canvas.delete(txt)))

    def _inject_bad_crc(self):
        if not self.last_frame:
            self._log("No last frame to inject into")
            return
        try:
            mid = self.last_frame[1:-1]
            un = unstuff_bytes(mid)
            crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1

            if len(un) < 1 + crc_size:
                return

            data_end = len(un) - 1 - crc_size
            un_list = bytearray(un)

            if crc_size == 2:
                current_crc = int.from_bytes(un_list[1+data_end:1+data_end+2], byteorder='big')
                new_crc = current_crc ^ 0xFFFF
                un_list[1+data_end:1+data_end+2] = new_crc.to_bytes(2, byteorder='big')
            else:
                un_list[1+data_end] ^= 0xFF

            new_mid = stuff_bytes(bytes(un_list))
            new_frame = bytes([FLAG]) + new_mid + bytes([FLAG])
            self._log("Injected Bad CRC")
            self.last_frame = new_frame
            self._process_frame(new_frame)
        except Exception:
            pass

    def _inject_bad_length(self):
        if not self.last_frame:
            self._log("No last frame to inject into")
            return
        try:
            mid = self.last_frame[1:-1]
            un = unstuff_bytes(mid)
            if len(un) < 2:
                return
            un_list = bytearray(un)
            un_list[0] = (un_list[0] + 2) & 0xFF
            new_mid = stuff_bytes(bytes(un_list))
            new_frame = bytes([FLAG]) + new_mid + bytes([FLAG])
            self._log("Injected Bad Length")
            self.last_frame = new_frame
            self._process_frame(new_frame)
        except Exception:
            pass

    def _inject_cut_data(self):
        if not self.last_frame:
            self._log("No last frame to inject into")
            return
        try:
            truncated = self.last_frame[:-1]
            self._log("Injected Cut Data (removed end flag)")
            self.last_frame = truncated
            self._process_frame(truncated)
        except Exception:
            pass

    def _paste_correct_example(self):
        data = b"Hi"
        polynomial = int(self.poly_var.get(), 16)
        crc = compute_crc(data, polynomial, self.crc_type.get())
        crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1

        if crc_size == 2:
            crc_bytes = crc.to_bytes(2, byteorder='big')
        else:
            crc_bytes = bytes([crc & 0xFF])

        mid = bytes([len(data)]) + data + crc_bytes
        frame = bytes([FLAG]) + stuff_bytes(mid) + bytes([FLAG])
        self._open_sim_dialog_with_hex(bytes_to_hex(frame))

    def _paste_badcrc_example(self):
        data = b"Hi"
        polynomial = int(self.poly_var.get(), 16)
        crc = compute_crc(data, polynomial, self.crc_type.get())
        crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1

        bad_crc = crc ^ (0xFFFF if crc_size == 2 else 0xFF)

        if crc_size == 2:
            crc_bytes = bad_crc.to_bytes(2, byteorder='big')
        else:
            crc_bytes = bytes([bad_crc & 0xFF])

        mid = bytes([len(data)]) + data + crc_bytes
        frame = bytes([FLAG]) + stuff_bytes(mid) + bytes([FLAG])
        self._open_sim_dialog_with_hex(bytes_to_hex(frame))

    def _paste_badlen_example(self):
        data = b"Hi"
        polynomial = int(self.poly_var.get(), 16)
        crc = compute_crc(data, polynomial, self.crc_type.get())
        crc_size = 2 if self.crc_type.get().startswith("CRC-16") else 1

        if crc_size == 2:
            crc_bytes = crc.to_bytes(2, byteorder='big')
        else:
            crc_bytes = bytes([crc & 0xFF])

        mid = bytes([(len(data) + 3) & 0xFF]) + data + crc_bytes
        frame = bytes([FLAG]) + stuff_bytes(mid) + bytes([FLAG])
        self._open_sim_dialog_with_hex(bytes_to_hex(frame))

    def _open_simulate_dialog(self):
        self._open_sim_dialog_with_hex("")

    def _open_sim_dialog_with_hex(self, initial_hex):
        dlg = tk.Toplevel(self.root)
        dlg.title("Simulate incoming hex")
        dlg.geometry("560x240")
        ttk.Label(dlg, text="Paste hex bytes (space separated), e.g.: 7E 02 48 49 F1 7E").pack(padx=8, pady=6)
        txt = tk.Text(dlg, height=8, width=64)
        txt.pack(padx=8)
        if initial_hex:
            txt.insert("end", initial_hex)
        def do_send():
            s = txt.get("1.0", "end").strip()
            dlg.destroy()
            if not s:
                return
            try:
                parts = s.split()
                data = bytes(int(p,16) for p in parts)
                self._on_bytes_received(data)
            except Exception:
                pass
        ttk.Button(dlg, text="Send to receiver", command=do_send).pack(pady=8)

    def _clear_display(self):
        self.raw_stream.delete("1.0", "end")
        for ch in self.steps_frame.winfo_children():
            ch.destroy()
        self._recv_buf = bytearray()
        self._clear_packet_texts()
        self._reset_box_borders()
        self.error_label.config(text="")
        self._reset_verification_steps()
        self._log("Cleared display")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def root_after(self, fn):
        self.root.after(1, fn)

def main():
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()