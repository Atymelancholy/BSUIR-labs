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
    "flag": "#cfe9ff",
    "length": "#ffd7a6",
    "data": "#d8f8d8",
    "fcs": "#f7d1d1",
    "highlight": "#9ee7ff",
    "error": "#ff9090",
    "correct": "#90ff90",
    "border": "#777777",
    "correct_bg": "#f0fff0",
    "error_bg": "#fff0f0"
}

def bytes_to_hex(bts: bytes) -> str:
    return " ".join(f"{x:02X}" for x in bts)

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

def compute_fcs(data: bytes) -> int:
    return sum(data) % 256

class SenderApp:
    def __init__(self, root):
        self.root = root
        root.title("Sender — Variant 2 (Byte-stuffing)")
        root.geometry("1000x800")

        self.serial_obj = None
        self.last_frame = None
        self.original_data = None

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")

        ctrl = ttk.Labelframe(top, text="Controls", padding=8)
        ctrl.pack(side="left", fill="y", padx=(0,8), ipadx=4)

        ttk.Label(ctrl, text="Mode:").pack(anchor="w")
        self.mode_var = tk.StringVar(value="serial" if SERIAL_AVAILABLE else "udp")
        ttk.Radiobutton(ctrl, text="Serial (COM)", variable=self.mode_var, value="serial").pack(anchor="w")
        ttk.Radiobutton(ctrl, text="UDP", variable=self.mode_var, value="udp").pack(anchor="w")

        ttk.Label(ctrl, text="COM port:").pack(anchor="w", pady=(6,0))
        self.port_combo = ttk.Combobox(ctrl, state="readonly", width=18)
        self.port_combo['values'] = self._get_serial_ports()
        if self.port_combo['values']:
            self.port_combo.current(0)
        self.port_combo.pack(fill="x")

        ttk.Label(ctrl, text="Baudrate:").pack(anchor="w", pady=(6,0))
        self.baud_combo = ttk.Combobox(ctrl, values=[9600, 19200, 38400, 57600, 115200], state="readonly", width=10)
        self.baud_combo.set(9600)
        self.baud_combo.pack(fill="x")

        ttk.Label(ctrl, text="UDP target host:").pack(anchor="w", pady=(8,0))
        self.host_entry = ttk.Entry(ctrl)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(fill="x")

        ttk.Label(ctrl, text="UDP target port:").pack(anchor="w", pady=(6,0))
        self.port_entry = ttk.Entry(ctrl)
        self.port_entry.insert(0, "5006")
        self.port_entry.pack(fill="x")

        ttk.Label(ctrl, text="Data (text or hex):").pack(anchor="w", pady=(8,0))
        self.input_mode = tk.StringVar(value="text")
        rbframe = ttk.Frame(ctrl)
        rbframe.pack(fill="x")
        ttk.Radiobutton(rbframe, text="Text (UTF-8)", variable=self.input_mode, value="text").pack(side="left")
        ttk.Radiobutton(rbframe, text="Hex (space separated)", variable=self.input_mode, value="hex").pack(side="left")

        self.data_entry = tk.Text(ctrl, height=5, width=30)
        self.data_entry.pack(pady=(6,0))

        ttk.Button(ctrl, text="Send Correct", command=lambda: self._on_send(mode="ok")).pack(fill="x", pady=6)
        ttk.Button(ctrl, text="Show: Bad FCS", command=lambda: self._show_comparison("bad_fcs")).pack(fill="x", pady=2)  # Изменено
        ttk.Button(ctrl, text="Show: Bad Length", command=lambda: self._show_comparison("bad_len")).pack(fill="x", pady=2)
        ttk.Button(ctrl, text="Send Bad FCS", command=lambda: self._on_send(mode="bad_fcs")).pack(fill="x", pady=2)  # Изменено
        ttk.Button(ctrl, text="Send Bad Length", command=lambda: self._on_send(mode="bad_len")).pack(fill="x", pady=2)

        ttk.Separator(ctrl).pack(fill="x", pady=8)
        ttk.Button(ctrl, text="Refresh COM ports", command=self._refresh_ports).pack(fill="x", pady=6)
        ttk.Button(ctrl, text="Clear log", command=lambda: self.log_text.delete("1.0","end")).pack(fill="x", pady=2)

        vis = ttk.Labelframe(top, text="Packet Visualization", padding=8)
        vis.pack(side="left", fill="both", expand=True)

        self.main_frame = ttk.LabelFrame(vis, text="Current Frame", padding=8)
        self.main_frame.pack(fill="x", pady=(0, 4))

        self.status_label = ttk.Label(self.main_frame, text="Ready to send...", foreground="blue")
        self.status_label.pack(anchor="w")

        self.main_canvas = tk.Canvas(self.main_frame, height=100, bg="white")
        self.main_canvas.pack(fill="x", pady=4)

        self.main_text = scrolledtext.ScrolledText(self.main_frame, height=3)
        self.main_text.pack(fill="x")

        self.comparison_frame = ttk.LabelFrame(vis, text="Error Comparison", padding=8)

        self.diff_frame = ttk.LabelFrame(vis, text="Analysis", padding=8)
        self.diff_frame.pack(fill="x", pady=6)
        self.diff_text = scrolledtext.ScrolledText(self.diff_frame, height=3)
        self.diff_text.pack(fill="x")
        self.diff_text.insert("1.0", "No analysis to show. Send a frame or click comparison buttons.")
        self.diff_text.config(state="disabled")

        ttk.Label(main, text="Log:").pack(anchor="w", pady=(6,0))
        self.log_text = scrolledtext.ScrolledText(main, height=8)
        self.log_text.pack(fill="both", expand=True)

        self._log("Sender ready")
        if not SERIAL_AVAILABLE:
            self._log("pyserial not found — Serial mode disabled (use UDP or install pyserial).")

    def _get_serial_ports(self):
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def _refresh_ports(self):
        self.port_combo['values'] = self._get_serial_ports()
        if self.port_combo['values']:
            self.port_combo.current(0)

    def _show_comparison(self, error_type):
        raw_bytes = self._get_input_data()
        if raw_bytes is None:
            return

        correct_frame, _, correct_values = self._build_frame(raw_bytes, bad_fcs=False, bad_len=False)
        error_frame, flags, _ = self._build_frame(raw_bytes,
                                                  bad_fcs=(error_type=="bad_fcs"),
                                                  bad_len=(error_type=="bad_len"))

        self._display_single_frame(correct_frame, "✓ CORRECT FRAME - How it should be", "green")

        self._create_comparison_area()
        self._display_comparison_in_area(error_frame, correct_values, error_type)

        error_name = "Bad FCS" if error_type == "bad_fcs" else "Bad Length"
        self._log(f"Showing comparison: Correct vs {error_name}")

    def _create_comparison_area(self):
        if not hasattr(self, 'comparison_frame_created') or not self.comparison_frame_created:
            self.comparison_frame.pack(fill="x", pady=4)
            self.comparison_frame_created = True

            ttk.Label(self.comparison_frame, text="✗ ERROR FRAME - What would be sent with error", foreground="red").pack(anchor="w")
            self.error_canvas = tk.Canvas(self.comparison_frame, height=100, bg=COLORS["error_bg"])
            self.error_canvas.pack(fill="x", pady=4)
            self.error_text = scrolledtext.ScrolledText(self.comparison_frame, height=3)
            self.error_text.pack(fill="x")

    def _display_comparison_in_area(self, error_frame: bytes, correct_values: dict, error_type: str):
        self.error_canvas.delete("all")
        self.error_text.delete("1.0", "end")
        self.diff_text.config(state="normal")
        self.diff_text.delete("1.0", "end")

        error_parsed = self._parse_frame(error_frame)

        self._draw_frame(self.error_canvas, error_parsed, is_correct=False)
        self.error_text.insert("end", f"Hex: {bytes_to_hex(error_frame)}\n")
        self.error_text.insert("end", f"Length: {error_parsed['length']:02X} | Data: {bytes_to_hex(error_parsed['data'])} | FCS: {error_parsed['fcs']:02X} ✗")  # Изменено

        correct_parsed = self._parse_frame(self.last_frame) if self.last_frame else error_parsed
        differences = self._find_differences(correct_parsed, error_parsed, correct_values, error_type)
        self.diff_text.insert("end", differences)
        self.diff_text.config(state="disabled")

    def _display_single_frame(self, frame: bytes, title: str, color: str):
        self.status_label.config(text=title, foreground=color)
        self.main_canvas.delete("all")
        self.main_text.delete("1.0", "end")

        parsed = self._parse_frame(frame)
        self._draw_frame(self.main_canvas, parsed, is_correct=(color=="green"))

        self.main_text.insert("end", f"Hex: {bytes_to_hex(frame)}\n")
        self.main_text.insert("end", f"Length: {parsed['length']:02X} | Data: {bytes_to_hex(parsed['data'])} | FCS: {parsed['fcs']:02X}")  # Изменено
        if color == "green":
            self.main_text.insert("end", " ✓")
        else:
            self.main_text.insert("end", " ✗")

    def _parse_frame(self, frame: bytes) -> dict:
        mid = frame[1:-1]
        un = unstuff_bytes(mid)
        if len(un) >= 2:
            length = un[0]
            data = un[1:-1]
            fcs = un[-1]
        else:
            length = 0
            data = b""
            fcs = 0

        return {
            'frame': frame,
            'length': length,
            'data': data,
            'fcs': fcs
        }

    def _draw_frame(self, canvas, parsed: dict, is_correct: bool):
        w = canvas.winfo_width() or 600
        h = 80
        gap = 8

        labels = [("Flag", COLORS["flag"]), ("Len", COLORS["length"]),
                  ("Data", COLORS["data"]), ("FCS", COLORS["fcs"]),
                  ("Flag", COLORS["flag"])]

        total = len(labels)
        boxw = max(90, (w - 20 - (total-1)*gap) // total)
        x = 10

        frame = parsed['frame']

        field_values = [
            f"{frame[0]:02X}",
            f"{parsed['length']:02X}",
            bytes_to_hex(parsed['data'])[:25] + ("..." if len(parsed['data']) > 4 else ""),
            f"{parsed['fcs']:02X}",
            f"{frame[-1]:02X}"
        ]

        for i, ((name, color), value) in enumerate(zip(labels, field_values)):
            outline_color = COLORS["correct"] if is_correct else COLORS["error"]
            outline_width = 3 if not is_correct else 2

            rect = canvas.create_rectangle(x, 20, x+boxw, 20+h, fill=color,
                                           outline=outline_color, width=outline_width)

            canvas.create_text(x+4, 24, anchor="nw", text=name,
                               font=("TkDefaultFont", 8, "bold"))

            canvas.create_text(x+4, 45, anchor="nw", text=value,
                               font=("TkDefaultFont", 8), width=boxw-8)

            x += boxw + gap

    def _find_differences(self, correct: dict, error: dict, correct_values: dict, error_type: str) -> str:
        differences = []

        if error_type == "bad_fcs":
            differences.append("ERROR TYPE: Bad FCS\n\n")

            data_changed = False
            if correct['data'] != error['data']:
                for i, (c_byte, e_byte) in enumerate(zip(correct['data'], error['data'])):
                    if c_byte != e_byte:
                        differences.append(f"• Data byte [{i}] was modified: {c_byte:02X} → {e_byte:02X}")
                        data_changed = True
                        break
                if not data_changed and len(correct['data']) != len(error['data']):
                    differences.append("• Data length was changed")

            if correct['fcs'] != error['fcs']:
                differences.append(f"• FCS is wrong: {correct['fcs']:02X} → {error['fcs']:02X}")

            differences.append(f"\nResult: Receiver will detect FCS error and reject the frame!")

        elif error_type == "bad_len":
            differences.append("ERROR TYPE: Bad Length\n\n")

            if correct['length'] != error['length']:
                differences.append(f"• Length field is wrong: {correct['length']:02X} → {error['length']:02X}")

            if correct['data'] != error['data']:
                differences.append("• Data was truncated or modified due to length change")

            if correct['fcs'] != error['fcs']:
                differences.append(f"• FCS also changed: {correct['fcs']:02X} → {error['fcs']:02X}")

            differences.append(f"\nResult: Receiver will detect length mismatch and reject the frame!")

        return "\n".join(differences)

    def _get_input_data(self):
        txt = self.data_entry.get("1.0", "end").strip()
        if not txt:
            messagebox.showwarning("No data", "Введите данные (текст или hex).")
            return None
        try:
            if self.input_mode.get() == "text":
                return txt.encode("utf-8")
            else:
                parts = txt.split()
                return bytes(int(p,16) for p in parts)
        except Exception as e:
            messagebox.showerror("Bad input", f"Не удалось разобрать ввод: {e}")
            return None

    def _on_send(self, mode="ok"):
        raw_bytes = self._get_input_data()
        if raw_bytes is None:
            return

        bad_fcs = (mode=="bad_fcs")
        bad_len = (mode=="bad_len")

        frame, flags, correct_values = self._build_frame(raw_bytes, bad_fcs=bad_fcs, bad_len=bad_len)
        self.last_frame = frame

        if mode == "ok":
            self._display_single_frame(frame, "✓ Sending CORRECT frame", "green")
            self._log("✅ Sent CORRECT frame")

            if hasattr(self, 'comparison_frame_created') and self.comparison_frame_created:
                self.comparison_frame.pack_forget()
                self.comparison_frame_created = False

            self.diff_text.config(state="normal")
            self.diff_text.delete("1.0", "end")
            self.diff_text.insert("end", "✓ FRAME ANALYSIS:\n\n")
            self.diff_text.insert("end", f"• Length field: {len(raw_bytes):02X} (matches actual data length)\n")
            self.diff_text.insert("end", f"• Data: {len(raw_bytes)} byte(s) correctly encoded\n")
            self.diff_text.insert("end", f"• FCS: {compute_fcs(raw_bytes):02X} (correctly computed)\n")  # Изменено
            self.diff_text.insert("end", f"• Byte stuffing: Applied to special bytes (FLAG, ESC)")
            self.diff_text.config(state="disabled")

        elif mode == "bad_fcs":
            self._display_single_frame(frame, "⚠ Sending BAD FCS frame", "orange")
            self._log("⚠ Sent BAD FCS frame")
        elif mode == "bad_len":
            self._display_single_frame(frame, "⚠ Sending BAD LENGTH frame", "orange")
            self._log("⚠ Sent BAD LENGTH frame")

        threading.Thread(target=self._send_frame, args=(frame,), daemon=True).start()

    def _build_frame(self, data: bytes, bad_fcs=False, bad_len=False):
        length = len(data)
        fcs = compute_fcs(data)

        correct_values = {
            "length": length,
            "data": data,
            "fcs": fcs
        }

        modified_data = bytearray(data)
        modified_fcs = fcs

        if bad_fcs:
            if len(modified_data) > 0:
                modified_data[0] = (modified_data[0] ^ 0xFF)
                modified_fcs = compute_fcs(modified_data)
            else:
                modified_data.append(0xAA)
                modified_fcs = compute_fcs(modified_data)

        if bad_len:
            length = (length + 2)
            if len(modified_data) > 1:
                modified_data.pop()
            else:
                modified_data.append(0x00)

        actual_data = modified_data if (bad_fcs or bad_len) else data
        actual_fcs = modified_fcs if bad_fcs else fcs

        if bad_len and not bad_fcs:
            actual_fcs = compute_fcs(actual_data)

        mid = bytes([length]) + bytes(actual_data) + bytes([actual_fcs])
        stuffed = stuff_bytes(mid)
        frame = bytes([FLAG]) + stuffed + bytes([FLAG])
        return frame, {"bad_fcs": bad_fcs, "bad_len": bad_len}, correct_values

    def _send_frame(self, frame: bytes):
        mode = self.mode_var.get()
        if mode == "serial":
            if not SERIAL_AVAILABLE:
                self._log("pyserial not available: cannot send over Serial")
                return
            port = self.port_combo.get()
            baud = int(self.baud_combo.get())
            try:
                with serial.Serial(port, baudrate=baud, timeout=0.2) as ser:
                    ser.write(frame)
                self._log(f"Sent over Serial {port}@{baud}")
            except Exception as e:
                self._log(f"Serial send error: {e}")
        else:
            host = self.host_entry.get().strip()
            port = int(self.port_entry.get().strip())
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(frame, (host, port))
            sock.close()
            self._log(f"Sent over UDP to {host}:{port}")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

def main():
    root = tk.Tk()
    app = SenderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()