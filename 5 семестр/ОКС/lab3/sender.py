
"""
Sender + CRC Visualization with Error Injection
Three-layer frame visualization with CRC error detection
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading
import socket
import random

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
    "crc": "#e6d1f7",
    "highlight": "#9ee7ff",
    "error": "#ffb3b3",
    "correct": "#90ff90",
    "border": "#777777",
    "correct_bg": "#f0fff0",
    "error_bg": "#fff0f0",
    "stuffed": "#ffebcd",
    "escaped": "#ffb6c1",
    "error_byte": "#ffcccc",
    "underline": "#ff0000"
}

CRC_POLYNOMIALS = {
    "CRC-8": 0x07,
    "CRC-16-CCITT": 0x1021,
    "CRC-16": 0x8005,
    "CRC-32": 0x04C11DB7,
    "Custom": 0x00
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

def compute_fcs_simple(data: bytes) -> int:
    return sum(data) & 0xFFFF

def compute_crc_division(data: bytes, polynomial: int, crc_type: str, crc_bits: int = None):
    if crc_bits is None:
        if crc_type == "CRC-8":
            crc_bits = 8
        elif crc_type == "CRC-16-CCITT" or crc_type == "CRC-16":
            crc_bits = 16
        elif crc_type == "CRC-32":
            crc_bits = 32
        else:
            crc_bits = 8

    polynomial = polynomial | (1 << crc_bits)
    polynomial = polynomial & ((1 << (crc_bits + 1)) - 1)

    data_bits = ''.join(format(b, '08b') for b in data)
    dividend = data_bits + ('0' * crc_bits)
    poly_bits = format(polynomial, f'0{crc_bits + 1}b')

    current = list(dividend)
    steps = []
    max_pos = len(data_bits)

    for pos in range(max_pos):
        window = ''.join(current[pos: pos + crc_bits + 1])
        if window[0] == '1':
            res = []
            for i in range(crc_bits + 1):
                res.append('0' if window[i] == poly_bits[i] else '1')
            for i in range(crc_bits + 1):
                current[pos + i] = res[i]
            steps.append({
                'position': pos,
                'current_bits': window,
                'poly_bits': poly_bits,
                'result_bits': ''.join(res)
            })

    remainder = ''.join(current[-crc_bits:]) if crc_bits > 0 else ''
    crc_value = int(remainder, 2) if remainder else 0
    return crc_value, steps, dividend, ''.join(current)

def compute_crc(data: bytes, polynomial: int, crc_type: str, crc_bits: int = None) -> int:
    if crc_bits is None:
        if crc_type == "CRC-8":
            crc_bits = 8
        elif crc_type == "CRC-16-CCITT" or crc_type == "CRC-16":
            crc_bits = 16
        elif crc_type == "CRC-32":
            crc_bits = 32
        else:
            crc_bits = 8

    polynomial = polynomial | (1 << crc_bits)

    if crc_bits == 8:
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    elif crc_bits == 16:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc
    elif crc_bits == 32:
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
                crc &= 0xFFFFFFFF
        return crc
    else:
        crc_val, _, _, _ = compute_crc_division(data, polynomial & ~(1 << crc_bits), crc_type, crc_bits)
        return crc_val

class SenderApp:
    def __init__(self, root):
        self.root = root
        root.title("Sender — Frame Visualization with CRC")
        root.geometry("1400x1000")

        self.serial_obj = None
        self.last_frame = None
        self.last_correct_frame = None
        self.division_steps = []
        self.error_division_steps = []
        self.dividend_bits = ""
        self.error_dividend_bits = ""
        self.final_bits = ""
        self.error_final_bits = ""
        self.current_step = 0
        self.error_current_step = 0
        self.animating = False
        self.error_animating = False
        self.anim_after = None
        self.error_anim_after = None

        self.injected_error_bytes = []
        self.corrected_positions = []
        self.show_error_frame = False

        self.bit_w = 10
        self.left_margin = 10
        self.top_margin = 10
        self.line_height = 18
        self.division_y = self.top_margin
        self.error_division_y = self.top_margin

        self._build_ui()
        self._update_crc_settings_status()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        ctrl = ttk.Labelframe(left, text="Controls", padding=8)
        ctrl.pack(fill="y", padx=6, pady=6)

        ttk.Label(ctrl, text="CRC Type:").pack(anchor="w")
        self.crc_type = tk.StringVar(value="CRC-8")
        crc_combo = ttk.Combobox(ctrl, textvariable=self.crc_type,
                                 values=list(CRC_POLYNOMIALS.keys()),
                                 state="readonly", width=18)
        crc_combo.pack(fill="x")
        crc_combo.bind('<<ComboboxSelected>>', self._on_crc_change)

        poly_frame = ttk.Frame(ctrl)
        poly_frame.pack(fill="x", pady=(6,0))

        ttk.Label(poly_frame, text="Polynomial (hex):").grid(row=0, column=0, sticky="w")
        self.poly_var = tk.StringVar(value="0x07")
        poly_entry = ttk.Entry(poly_frame, textvariable=self.poly_var, width=10)
        poly_entry.grid(row=0, column=1, sticky="w", padx=(5,0))

        ttk.Label(poly_frame, text="Bits:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.crc_bits_var = tk.StringVar(value="8")
        crc_bits_combo = ttk.Combobox(poly_frame, textvariable=self.crc_bits_var,
                                      values=["4", "8", "16", "32", "64"],
                                      state="readonly", width=4)
        crc_bits_combo.grid(row=0, column=3, sticky="w", padx=(5,0))

        ttk.Separator(ctrl).pack(fill="x", pady=6)
        ttk.Label(ctrl, text="Data Block Length:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(6,0))

        length_frame = ttk.Frame(ctrl)
        length_frame.pack(fill="x", pady=4)

        self.block_length_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(length_frame, text="Auto (from data)", variable=self.block_length_mode,
                        value="auto", command=self._update_length_mode).pack(side="left", padx=(0,10))
        ttk.Radiobutton(length_frame, text="Fixed length:", variable=self.block_length_mode,
                        value="fixed", command=self._update_length_mode).pack(side="left")

        self.block_length_var = tk.StringVar(value="10")
        self.block_length_entry = ttk.Entry(length_frame, textvariable=self.block_length_var, width=6, state="disabled")
        self.block_length_entry.pack(side="left", padx=5)
        ttk.Label(length_frame, text="bytes").pack(side="left")

        ttk.Label(ctrl, text="Force Length field (optional):").pack(anchor="w", pady=(6,0))
        self.force_len_var = tk.StringVar(value="")
        ttk.Entry(ctrl, textvariable=self.force_len_var).pack(fill="x")

        ttk.Separator(ctrl).pack(fill="x", pady=6)

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
        self.baud_combo = ttk.Combobox(ctrl, values=[9600,19200,38400,57600,115200], state="readonly")
        self.baud_combo.set(9600)
        self.baud_combo.pack(fill="x")

        ttk.Label(ctrl, text="UDP target host:").pack(anchor="w", pady=(6,0))
        self.host_entry = ttk.Entry(ctrl)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(fill="x")

        ttk.Label(ctrl, text="UDP target port:").pack(anchor="w", pady=(6,0))
        self.port_entry = ttk.Entry(ctrl)
        self.port_entry.insert(0, "5006")
        self.port_entry.pack(fill="x")

        ttk.Separator(ctrl).pack(fill="x", pady=6)

        ttk.Label(ctrl, text="Data (text or hex):").pack(anchor="w")
        self.input_mode = tk.StringVar(value="text")
        imf = ttk.Frame(ctrl)
        imf.pack(fill="x")
        ttk.Radiobutton(imf, text="Text (UTF-8)", variable=self.input_mode, value="text").pack(side="left")
        ttk.Radiobutton(imf, text="Hex (space separated)", variable=self.input_mode, value="hex").pack(side="left")

        self.data_entry = tk.Text(ctrl, height=5, width=28)
        self.data_entry.pack(pady=(6,0))
        self.data_entry.insert("1.0", "Hello~World")

        ttk.Button(ctrl, text="Send Correct", command=lambda: self._on_send("ok")).pack(fill="x", pady=6)
        ttk.Button(ctrl, text="Send Bad CRC", command=lambda: self._on_send("bad_crc")).pack(fill="x", pady=2)
        ttk.Button(ctrl, text="Send Bad Length", command=lambda: self._on_send("bad_len")).pack(fill="x", pady=2)

        ttk.Separator(ctrl).pack(fill="x", pady=6)

        error_ctrl = ttk.Labelframe(ctrl, text="Error Injection", padding=6)
        error_ctrl.pack(fill="x", pady=6)

        ttk.Label(error_ctrl, text="Manual Error Injection:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(0,4))

        manual_frame = ttk.Frame(error_ctrl)
        manual_frame.pack(fill="x", pady=2)

        ttk.Label(manual_frame, text="Byte position:").grid(row=0, column=0, sticky="w", padx=(0,5))
        self.inj_byte_idx = tk.StringVar(value="0")
        ttk.Entry(manual_frame, textvariable=self.inj_byte_idx, width=8).grid(row=0, column=1, sticky="w", padx=(0,10))

        ttk.Label(manual_frame, text="New value (hex):").grid(row=0, column=2, sticky="w", padx=(0,5))
        self.inj_byte_val = tk.StringVar(value="")
        ttk.Entry(manual_frame, textvariable=self.inj_byte_val, width=8).grid(row=0, column=3, sticky="w", padx=(0,10))

        ttk.Button(manual_frame, text="Add Error", command=self._inject_at_position, width=10).grid(row=0, column=4, sticky="w")

        auto_frame = ttk.Frame(error_ctrl)
        auto_frame.pack(fill="x", pady=4)

        ttk.Label(auto_frame, text="Auto Error Generation:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4,2))

        auto_btn_frame = ttk.Frame(auto_frame)
        auto_btn_frame.pack(fill="x", pady=2)

        ttk.Button(auto_btn_frame, text="Single Random Error", command=self._inject_random_single_error, width=16).pack(side="left", padx=(0,5))
        ttk.Button(auto_btn_frame, text="Multiple Errors (1-3)", command=self._inject_random_multiple_errors, width=16).pack(side="left", padx=5)
        ttk.Button(auto_btn_frame, text="Bit Flip Error", command=self._inject_random_bit_flip, width=16).pack(side="left", padx=5)

        manage_frame = ttk.Frame(error_ctrl)
        manage_frame.pack(fill="x", pady=4)

        ttk.Label(manage_frame, text="Error Management:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w", pady=(4,2))

        manage_btn_frame = ttk.Frame(manage_frame)
        manage_btn_frame.pack(fill="x", pady=2)

        ttk.Button(manage_btn_frame, text="Clear All Errors", command=self._clear_all_errors, width=16).pack(side="left", padx=(0,5))
        ttk.Button(manage_btn_frame, text="Show Error List", command=self._show_error_list, width=16).pack(side="left", padx=5)

        self.error_status = ttk.Label(error_ctrl, text="No errors injected", foreground="green", font=("TkDefaultFont", 8))
        self.error_status.pack(anchor="w", pady=(4,0))

        ttk.Separator(ctrl).pack(fill="x", pady=6)

        ttk.Button(ctrl, text="Try Auto-correct (single-bit)", command=self._try_autocorrect).pack(fill="x", pady=2)
        ttk.Button(ctrl, text="Refresh COM ports", command=self._refresh_ports).pack(fill="x", pady=2)
        ttk.Button(ctrl, text="Clear log", command=lambda: self.log_text.delete("1.0","end")).pack(fill="x", pady=2)

        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True, padx=6)

        comparison_frame = ttk.Labelframe(center, text="Packet Visualization", padding=8)
        comparison_frame.pack(fill="x", pady=(0,6))

        ttk.Label(comparison_frame, text="🟢 Текущий пакет (с байт-стаффингом):", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        self.current_canvas = tk.Canvas(comparison_frame, height=70, bg="white")
        self.current_canvas.pack(fill="x", pady=2)
        self.current_text = scrolledtext.ScrolledText(comparison_frame, height=2)
        self.current_text.pack(fill="x", pady=(0,6))

        ttk.Label(comparison_frame, text="✅ Правильный пакет (без стаффинга):", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        self.correct_canvas = tk.Canvas(comparison_frame, height=70, bg=COLORS["correct_bg"])
        self.correct_canvas.pack(fill="x", pady=2)
        self.correct_text = scrolledtext.ScrolledText(comparison_frame, height=2)
        self.correct_text.pack(fill="x", pady=(0,6))

        self.error_label = ttk.Label(comparison_frame, text="❌ Ошибочный пакет (подсветка ошибок):", font=("TkDefaultFont", 9, "bold"))
        self.error_canvas = tk.Canvas(comparison_frame, height=70, bg=COLORS["error_bg"])
        self.error_text = scrolledtext.ScrolledText(comparison_frame, height=2)

        status_frame = ttk.Labelframe(center, text="Status", padding=8)
        status_frame.pack(fill="x", pady=(6,0))

        status_left = ttk.Frame(status_frame)
        status_left.pack(side="left", fill="x", expand=True)

        status_right = ttk.Frame(status_frame)
        status_right.pack(side="right", fill="x", expand=True)

        self.status_label = ttk.Label(status_left, text="Ready", foreground="blue", font=("TkDefaultFont", 10, "bold"))
        self.status_label.pack(anchor="w")

        self.crc_status_label = ttk.Label(status_left, text="CRC: Not checked", foreground="black", font=("TkDefaultFont", 9))
        self.crc_status_label.pack(anchor="w")

        self.block_status_label = ttk.Label(status_right, text="Block length: Auto", foreground="purple", font=("TkDefaultFont", 9))
        self.block_status_label.pack(anchor="w")

        self.crc_settings_label = ttk.Label(status_right, text="CRC: 8-bit, Poly: 0x07", foreground="darkgreen", font=("TkDefaultFont", 9))
        self.crc_settings_label.pack(anchor="w")

        bottomvis = ttk.Labelframe(center, text="CRC Division Visualization (Ladder) - Two Panels", padding=8)
        bottomvis.pack(fill="both", expand=True, pady=(6,0))

        division_container = ttk.Frame(bottomvis)
        division_container.pack(fill="both", expand=True)

        left_division = ttk.Labelframe(division_container, text="✅ Correct CRC Calculation", padding=4)
        left_division.pack(side="left", fill="both", expand=True, padx=(0,2))

        cv_wrap_left = ttk.Frame(left_division)
        cv_wrap_left.pack(fill="both", expand=True)

        self.division_canvas = tk.Canvas(cv_wrap_left, bg="white", height=200)
        self.hscroll_left = ttk.Scrollbar(cv_wrap_left, orient="horizontal", command=self.division_canvas.xview)
        self.vscroll_left = ttk.Scrollbar(cv_wrap_left, orient="vertical", command=self.division_canvas.yview)
        self.division_canvas.configure(xscrollcommand=self.hscroll_left.set, yscrollcommand=self.vscroll_left.set)

        self.division_canvas.grid(row=0, column=0, sticky="nsew")
        self.vscroll_left.grid(row=0, column=1, sticky="ns")
        self.hscroll_left.grid(row=1, column=0, sticky="ew")
        cv_wrap_left.rowconfigure(0, weight=1)
        cv_wrap_left.columnconfigure(0, weight=1)
        self.division_canvas.bind("<Configure>", lambda e: self.division_canvas.configure(scrollregion=self.division_canvas.bbox("all")))

        right_division = ttk.Labelframe(division_container, text="❌ Error CRC Calculation", padding=4)
        right_division.pack(side="right", fill="both", expand=True, padx=(2,0))

        cv_wrap_right = ttk.Frame(right_division)
        cv_wrap_right.pack(fill="both", expand=True)

        self.error_division_canvas = tk.Canvas(cv_wrap_right, bg="white", height=200)
        self.hscroll_right = ttk.Scrollbar(cv_wrap_right, orient="horizontal", command=self.error_division_canvas.xview)
        self.vscroll_right = ttk.Scrollbar(cv_wrap_right, orient="vertical", command=self.error_division_canvas.yview)
        self.error_division_canvas.configure(xscrollcommand=self.hscroll_right.set, yscrollcommand=self.vscroll_right.set)

        self.error_division_canvas.grid(row=0, column=0, sticky="nsew")
        self.vscroll_right.grid(row=0, column=1, sticky="ns")
        self.hscroll_right.grid(row=1, column=0, sticky="ew")
        cv_wrap_right.rowconfigure(0, weight=1)
        cv_wrap_right.columnconfigure(0, weight=1)
        self.error_division_canvas.bind("<Configure>", lambda e: self.error_division_canvas.configure(scrollregion=self.error_division_canvas.bbox("all")))

        anim_ctrl = ttk.Frame(bottomvis)
        anim_ctrl.pack(fill="x", pady=6)

        left_ctrl = ttk.Frame(anim_ctrl)
        left_ctrl.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Label(left_ctrl, text="Correct CRC:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        left_btn_frame = ttk.Frame(left_ctrl)
        left_btn_frame.pack(fill="x", pady=2)
        ttk.Button(left_btn_frame, text="Prepare Steps", command=self._prepare_division).pack(side="left", padx=2)
        self.start_btn = ttk.Button(left_btn_frame, text="Start", command=self._start_animation)
        self.start_btn.pack(side="left", padx=2)
        ttk.Button(left_btn_frame, text="Pause", command=self._pause_animation).pack(side="left", padx=2)
        ttk.Button(left_btn_frame, text="Next", command=self._next_division_step).pack(side="left", padx=2)
        ttk.Button(left_btn_frame, text="Reset", command=self._reset_division_steps).pack(side="left", padx=2)

        right_ctrl = ttk.Frame(anim_ctrl)
        right_ctrl.pack(side="right", fill="x", expand=True, padx=2)
        ttk.Label(right_ctrl, text="Error CRC:", font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        right_btn_frame = ttk.Frame(right_ctrl)
        right_btn_frame.pack(fill="x", pady=2)
        ttk.Button(right_btn_frame, text="Prepare Steps", command=self._prepare_error_division).pack(side="left", padx=2)
        self.error_start_btn = ttk.Button(right_btn_frame, text="Start", command=self._start_error_animation)
        self.error_start_btn.pack(side="left", padx=2)
        ttk.Button(right_btn_frame, text="Pause", command=self._pause_error_animation).pack(side="left", padx=2)
        ttk.Button(right_btn_frame, text="Next", command=self._next_error_division_step).pack(side="left", padx=2)
        ttk.Button(right_btn_frame, text="Reset", command=self._reset_error_division_steps).pack(side="left", padx=2)

        speed_frame = ttk.Frame(anim_ctrl)
        speed_frame.pack(side="bottom", fill="x", pady=(10,0))
        ttk.Label(speed_frame, text="Speed (both panels):").pack(side="left", padx=(10,2))
        self.speed_scale = ttk.Scale(speed_frame, from_=0.05, to=2.0, orient="horizontal")
        self.speed_scale.set(0.6)
        self.speed_scale.pack(side="left", padx=2, fill="x", expand=True)
        ttk.Label(speed_frame, text="sec/step").pack(side="left", padx=4)

        ops_area = ttk.Labelframe(center, text="Operations (step-by-step & status)", padding=6)
        ops_area.pack(fill="both", expand=False, pady=(6,0))
        self.steps_text = scrolledtext.ScrolledText(ops_area, height=5)
        self.steps_text.pack(fill="both", expand=True)
        self.steps_text.insert("1.0", "Operations will appear here...")
        self.steps_text.config(state="disabled")

        internal_area = ttk.Labelframe(center, text="Internal Log (intermediate calculations)", padding=6)
        internal_area.pack(fill="both", expand=True, pady=(6,0))
        self.internal_text = scrolledtext.ScrolledText(internal_area, height=5)
        self.internal_text.pack(fill="both", expand=True)
        self.internal_text.insert("1.0", "Internal steps will appear here...")
        self.internal_text.config(state="disabled")

        right = ttk.Frame(main, width=300)
        right.pack(side="left", fill="y", padx=6)

        diff = ttk.Labelframe(right, text="Analysis", padding=8)
        diff.pack(fill="x", pady=(0,6))
        self.diff_text = scrolledtext.ScrolledText(diff, height=8)
        self.diff_text.pack(fill="both", expand=True)
        self.diff_text.insert("1.0", "No analysis yet.")
        self.diff_text.config(state="disabled")

        ttk.Label(right, text="Log:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(right, height=12)
        self.log_text.pack(fill="both", expand=True)

        self._log("Sender ready")
        if not SERIAL_AVAILABLE:
            self._log("pyserial not found — Serial mode disabled (use UDP)")

    def _update_length_mode(self):
        if self.block_length_mode.get() == "fixed":
            self.block_length_entry.config(state="normal")
        else:
            self.block_length_entry.config(state="disabled")

    def _get_block_length(self):
        if self.block_length_mode.get() == "auto":
            return None
        else:
            try:
                length = int(self.block_length_var.get())
                return max(1, min(length, 255))
            except ValueError:
                messagebox.showerror("Invalid length", "Block length must be a number")
                return None

    def _get_crc_bits(self):
        try:
            return int(self.crc_bits_var.get())
        except ValueError:
            return 8

    def _get_polynomial(self):
        try:
            poly_str = self.poly_var.get().strip()
            if poly_str.startswith('0x') or poly_str.startswith('0X'):
                return int(poly_str, 16)
            else:
                return int(poly_str, 16)
        except ValueError:
            messagebox.showerror("Invalid polynomial", "Polynomial must be a valid hex number (e.g., 0x107)")
            return None

    def _prepare_data_with_block_length(self, raw_data: bytes) -> bytes:
        block_length = self._get_block_length()

        if block_length is None:
            return raw_data

        if len(raw_data) > block_length:
            self._log(f"Data truncated to {block_length} bytes (was {len(raw_data)} bytes)")
            return raw_data[:block_length]
        elif len(raw_data) < block_length:
            padding = bytes([0] * (block_length - len(raw_data)))
            self._log(f"Data padded to {block_length} bytes (was {len(raw_data)} bytes)")
            return raw_data + padding
        else:
            return raw_data

    def _on_crc_change(self, event=None):
        crc_type = self.crc_type.get()
        if crc_type == "Custom":
            self.poly_var.set("0x00")
            self.crc_bits_var.set("8")
        else:
            polynomial = CRC_POLYNOMIALS.get(crc_type, 0x07)
            if crc_type == "CRC-8":
                self.poly_var.set(f"0x{polynomial:02X}")
                self.crc_bits_var.set("8")
            elif crc_type == "CRC-16-CCITT" or crc_type == "CRC-16":
                self.poly_var.set(f"0x{polynomial:04X}")
                self.crc_bits_var.set("16")
            elif crc_type == "CRC-32":
                self.poly_var.set(f"0x{polynomial:08X}")
                self.crc_bits_var.set("32")

        self._update_crc_settings_status()

    def _update_crc_settings_status(self):
        crc_type = self.crc_type.get()
        crc_bits = self._get_crc_bits()
        poly = self._get_polynomial()
        if poly is not None:
            self.crc_settings_label.config(
                text=f"CRC: {crc_bits}-bit {crc_type}, Poly: 0x{poly:0{max(2, crc_bits//4)}X}"
            )

    def _get_serial_ports(self):
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def _refresh_ports(self):
        self.port_combo['values'] = self._get_serial_ports()
        if self.port_combo['values']:
            self.port_combo.current(0)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def _update_error_status(self):
        if not self.injected_error_bytes:
            self.error_status.config(text="No errors injected", foreground="green")
        else:
            error_positions = [pos for pos, _, _ in self.injected_error_bytes]
            self.error_status.config(text=f"Errors at positions: {sorted(error_positions)}", foreground="red")

    def _inject_at_position(self):
        raw = self._get_input_data()
        if raw is None:
            return

        try:
            idx = int(self.inj_byte_idx.get(), 0)
        except:
            messagebox.showerror("Bad index", "Byte index must be integer")
            return

        value_hex = self.inj_byte_val.get().strip()
        if value_hex == "":
            messagebox.showerror("No value", "Enter hex value for byte (e.g., 'FF')")
            return

        try:
            val = int(value_hex, 16) & 0xFF
        except:
            messagebox.showerror("Bad hex", "Invalid hex value")
            return

        if idx < 0 or idx >= len(raw):
            messagebox.showerror("Index out of range", f"Byte index must be 0..{len(raw)-1}")
            return

        old_val = raw[idx]

        self.injected_error_bytes = [err for err in self.injected_error_bytes if err[0] != idx]
        self.injected_error_bytes.append((idx, old_val, val))

        self._log(f"Injected manual error at byte {idx}: 0x{old_val:02X} → 0x{val:02X}")
        self._append_ops(f"Injected manual error at byte {idx}: 0x{old_val:02X} → 0x{val:02X}")
        self._update_error_status()
        self._on_send("ok")

    def _inject_random_single_error(self):
        raw = self._get_input_data()
        if raw is None or len(raw) == 0:
            return

        pos = random.randint(0, len(raw)-1)
        val = random.randint(0, 255)
        old_val = raw[pos]

        self.injected_error_bytes = [err for err in self.injected_error_bytes if err[0] != pos]
        self.injected_error_bytes.append((pos, old_val, val))

        self._log(f"Injected random single error at byte {pos}: 0x{old_val:02X} → 0x{val:02X}")
        self._append_ops(f"Injected random single error at byte {pos}: 0x{old_val:02X} → 0x{val:02X}")
        self._update_error_status()
        self._on_send("ok")

    def _inject_random_multiple_errors(self):
        raw = self._get_input_data()
        if raw is None or len(raw) == 0:
            return

        num_errors = random.randint(1, min(3, len(raw)))
        error_positions = random.sample(range(len(raw)), num_errors)

        changes = []
        for pos in error_positions:
            old_val = raw[pos]
            new_val = random.randint(0, 255)

            self.injected_error_bytes = [err for err in self.injected_error_bytes if err[0] != pos]
            self.injected_error_bytes.append((pos, old_val, new_val))
            changes.append(f"byte {pos}: 0x{old_val:02X}→0x{new_val:02X}")

        self._log(f"Injected {num_errors} random errors: {', '.join(changes)}")
        self._append_ops(f"Injected {num_errors} random errors")
        self._update_error_status()
        self._on_send("ok")

    def _inject_random_bit_flip(self):
        raw = self._get_input_data()
        if raw is None or len(raw) == 0:
            return

        pos = random.randint(0, len(raw)-1)
        bit_pos = random.randint(0, 7)

        old_val = raw[pos]
        new_val = old_val ^ (1 << bit_pos)

        self.injected_error_bytes = [err for err in self.injected_error_bytes if err[0] != pos]
        self.injected_error_bytes.append((pos, old_val, new_val))

        self._log(f"Injected bit flip at byte {pos}, bit {bit_pos}: 0x{old_val:02X} → 0x{new_val:02X}")
        self._append_ops(f"Injected bit flip at byte {pos}, bit {bit_pos}")
        self._update_error_status()
        self._on_send("ok")

    def _clear_all_errors(self):
        if not self.injected_error_bytes:
            messagebox.showinfo("No errors", "No errors to clear")
            return

        self.injected_error_bytes = []
        self.corrected_positions = []
        self._log("Cleared all injected errors")
        self._append_ops("Cleared all injected errors")
        self._update_error_status()
        self._on_send("ok")

    def _show_error_list(self):
        if not self.injected_error_bytes:
            messagebox.showinfo("Error List", "No errors injected")
            return

        error_list = "Current injected errors:\n\n"
        for idx, old_val, new_val in sorted(self.injected_error_bytes, key=lambda x: x[0]):
            error_list += f"Byte {idx}: 0x{old_val:02X} → 0x{new_val:02X}\n"

        messagebox.showinfo("Error List", error_list)

    def _apply_errors_to_data(self, data: bytes) -> bytes:
        if not self.injected_error_bytes:
            return data

        modified = bytearray(data)
        for idx, old_val, new_val in self.injected_error_bytes:
            if idx < len(modified):
                modified[idx] = new_val
        return bytes(modified)

    def _try_autocorrect(self):
        if not self.last_frame:
            messagebox.showinfo("No frame", "First prepare a frame (Send Correct) to compare with.")
            return

        parsed = self._parse_frame(self.last_frame)
        data_bytes = bytearray(parsed.get('data', b''))

        if not data_bytes:
            messagebox.showinfo("No data", "No data in current frame for correction.")
            return

        original_data = self._get_input_data()
        if original_data is None:
            return

        self._append_ops("Auto-correct: trying single-bit flips in data...")
        found = False
        found_pos = None
        found_bit = None

        for byte_idx in range(len(data_bytes)):
            for bit_idx in range(8):
                trial = bytearray(data_bytes)
                trial[byte_idx] ^= (1 << bit_idx)

                if byte_idx < len(original_data) and trial[byte_idx] == original_data[byte_idx]:
                    found = True
                    found_pos = byte_idx
                    found_bit = bit_idx
                    break
            if found:
                break

        if found:
            self.injected_error_bytes = [err for err in self.injected_error_bytes if err[0] != found_pos]
            self.corrected_positions.append((found_pos, found_bit))

            self._append_ops(f"Auto-correct found single-bit: byte {found_pos}, bit {found_bit}. Applied correction.")
            self._log(f"Auto-correct: corrected byte {found_pos} bit {found_bit}")
            self._on_send("ok")
        else:
            self._append_ops("Auto-correct: no single-bit correction found.")
            self._log("Auto-correct: not found")
            messagebox.showinfo("Auto-correct", "No single-bit errors found to correct.")

    def _get_input_data(self):
        txt = self.data_entry.get("1.0","end").strip()
        if not txt:
            messagebox.showwarning("No data","Enter data (text or hex).")
            return None
        try:
            if self.input_mode.get() == "text":
                raw_data = txt.encode("utf-8")
            else:
                parts = txt.split()
                raw_data = bytes(int(p,16) for p in parts)

            return self._prepare_data_with_block_length(raw_data)
        except Exception as e:
            messagebox.showerror("Bad input", f"Failed to parse input: {e}")
            return None

    def _build_frame(self, data: bytes, bad_crc=False, bad_len=False, apply_errors=False):
        length = len(data)
        polynomial = self._get_polynomial()
        if polynomial is None:
            return None, None

        crc_type = self.crc_type.get()
        crc_bits = self._get_crc_bits()

        if apply_errors:
            modified_data = self._apply_errors_to_data(data)
        else:
            modified_data = data

        fcs_value = compute_fcs_simple(modified_data)
        crc_value = compute_crc(modified_data, polynomial, crc_type, crc_bits)

        crc_size = (crc_bits + 7) // 8

        if bad_crc:
            crc_mask = (1 << crc_bits) - 1
            crc_value = crc_value ^ crc_mask

        if bad_len:
            length = (length + 2) & 0xFF
            if len(modified_data) > 1:
                temp_data = bytearray(modified_data)
                temp_data.pop()
                modified_data = bytes(temp_data)
            else:
                temp_data = bytearray(modified_data)
                temp_data.append(0x00)
                modified_data = bytes(temp_data)
            if not bad_crc:
                fcs_value = compute_fcs_simple(modified_data)
                crc_value = compute_crc(modified_data, polynomial, crc_type, crc_bits)

        if self.force_len_var.get().strip() != "":
            try:
                forced = int(self.force_len_var.get(), 0) & 0xFF
                length = forced
            except:
                pass

        fcs_bytes = fcs_value.to_bytes(2, byteorder='big')
        crc_bytes = crc_value.to_bytes(crc_size, byteorder='big')

        mid = bytes([length]) + bytes(modified_data) + fcs_bytes + crc_bytes
        stuffed = stuff_bytes(mid)
        frame = bytes([FLAG]) + stuffed + bytes([FLAG])

        return frame, {
            "length": length,
            "data": bytes(modified_data),
            "fcs": fcs_value,
            "crc": crc_value,
            "stuffed": stuffed,
            "mid": mid
        }

    def _parse_frame(self, frame: bytes) -> dict:
        if not frame or len(frame) < 2:
            return {'frame': frame, 'length':0, 'data':b'', 'fcs':b'', 'crc_received':b''}

        mid = frame[1:-1]
        un = unstuff_bytes(mid)
        length = 0
        data = b''
        fcs = b''
        crc_received = b''

        crc_bits = self._get_crc_bits()
        crc_size = (crc_bits + 7) // 8

        if len(un) >= 1:
            length = un[0]
            if len(un) >= 1 + 2 + crc_size:
                data_end = len(un) - 2 - crc_size
                if data_end > 1:
                    data = un[1:data_end]
                else:
                    data = b''
                fcs = un[data_end:data_end + 2]
                crc_received = un[data_end + 2:data_end + 2 + crc_size]
            elif len(un) >= 1 + 2:
                data_end = len(un) - 2
                if data_end > 1:
                    data = un[1:data_end]
                else:
                    data = b''
                fcs = un[data_end:data_end + 2]
            else:
                if len(un) > 1:
                    data = un[1:]
                else:
                    data = b''
                fcs = b''

        return {
            'frame': frame,
            'length': length,
            'data': data,
            'fcs': fcs,
            'crc_received': crc_received,
            'stuffed': mid
        }

    def _check_crc_correct_logic(self, parsed_frame: dict, original_crc: int) -> tuple:
        crc_received_bytes = parsed_frame.get('crc_received', b'')
        crc_bits = self._get_crc_bits()

        if not crc_received_bytes:
            return False, original_crc, 0

        received_crc = int.from_bytes(crc_received_bytes, byteorder='big')
        is_valid = (original_crc == received_crc)

        return is_valid, original_crc, received_crc

    def _draw_frame(self, canvas, parsed: dict, is_correct: bool, show_stuffing: bool = False, error_positions: list=None):
        canvas.delete("all")
        w = canvas.winfo_width() or 700
        h = 70
        gap = 8

        crc_bits = self._get_crc_bits()
        crc_size = (crc_bits + 7) // 8

        if show_stuffing:
            labels = [("Flag", COLORS["flag"]), ("Stuffed", COLORS["stuffed"]), ("Flag", COLORS["flag"])]
            box_widths = [80, w-180, 80]
        else:
            labels = [
                ("Flag", COLORS["flag"]),
                ("Len", COLORS["length"]),
                ("Data", COLORS["data"]),
                ("FCS\n(checksum)", COLORS["fcs"]),
                (f"CRC\n({crc_bits}-bit)", COLORS["crc"]),
                ("Flag", COLORS["flag"])
            ]
            box_widths = [60, 50, w-340, 100, 80, 60]

        x = 10

        if show_stuffing:
            frame = parsed.get('frame', b'')
            stuffed_data = parsed.get('stuffed', b'')
            field_values = [
                f"{frame[0]:02X}" if frame else "--",
                bytes_to_hex(stuffed_data),
                f"{frame[-1]:02X}" if frame else "--"
            ]
        else:
            frame = parsed.get('frame', b'')
            fcs_value = int.from_bytes(parsed.get('fcs', b''), byteorder='big') if parsed.get('fcs') else 0
            crc_received_bytes = parsed.get('crc_received', b'')
            crc_received = int.from_bytes(crc_received_bytes, byteorder='big') if crc_received_bytes else 0

            field_values = [
                f"{frame[0]:02X}" if frame else "--",
                f"{parsed.get('length',0):02X}",
                bytes_to_hex(parsed.get('data', b'')),
                f"{fcs_value:04X}",
                f"{crc_received:0{crc_size*2}X}",
                f"{frame[-1]:02X}" if frame else "--"
            ]

        for i, ((name, color), value, boxw) in enumerate(zip(labels, field_values, box_widths)):
            outline_color = COLORS["correct"] if is_correct else COLORS["error"]
            outline_width = 2 if is_correct else 3

            fill_color = color

            canvas.create_rectangle(x, 10, x+boxw, 10+h, fill=fill_color, outline=outline_color, width=outline_width)

            label_lines = name.split('\n')
            for j, line in enumerate(label_lines):
                canvas.create_text(x+4, 12 + j*10, anchor="nw", text=line, font=("TkDefaultFont", 8, "bold"))

            if show_stuffing and name == "Stuffed":
                stuffed_bytes = parsed.get('stuffed', b'')
                if stuffed_bytes:
                    bx = x+4
                    by = 36
                    inner_w = max(18, (boxw - 12) // max(1, len(stuffed_bytes)))
                    for idx, b in enumerate(stuffed_bytes):
                        byte_x = bx + idx * (inner_w + 2)
                        color_fill = "#ffffff"
                        if b == ESC:
                            color_fill = COLORS["escaped"]
                        elif idx > 0 and stuffed_bytes[idx-1] == ESC:
                            color_fill = COLORS["stuffed"]

                        canvas.create_rectangle(byte_x, by-2, byte_x+inner_w, by+14, fill=color_fill, outline="#444")
                        canvas.create_text(byte_x+2, by, anchor="nw", text=f"{b:02X}", font=("TkDefaultFont",8))
                else:
                    canvas.create_text(x+4, 45, anchor="nw", text=value, font=("TkDefaultFont", 8), width=boxw-8)
            elif not show_stuffing and name == "Data":
                data_bytes = parsed.get('data', b'')
                if data_bytes:
                    bx = x+4
                    by = 36
                    inner_w = max(18, (boxw - 12) // max(1, len(data_bytes)))
                    for idx, b in enumerate(data_bytes):
                        byte_x = bx + idx * (inner_w + 2)
                        color_fill = "#ffffff"

                        if error_positions and idx in error_positions and not is_correct:
                            color_fill = COLORS["error_byte"]
                            canvas.create_line(byte_x, by+14, byte_x+inner_w, by+14,
                                               fill=COLORS["underline"], width=2)

                        canvas.create_rectangle(byte_x, by-2, byte_x+inner_w, by+14, fill=color_fill, outline="#444")
                        canvas.create_text(byte_x+2, by, anchor="nw", text=f"{b:02X}", font=("TkDefaultFont",8))
                else:
                    canvas.create_text(x+4, 45, anchor="nw", text=value, font=("TkDefaultFont", 8), width=boxw-8)
            else:
                canvas.create_text(x+4, 45, anchor="nw", text=value, font=("TkDefaultFont", 8), width=boxw-8)
            x += boxw + gap

    def _draw_three_frame_comparison(self, current_parsed: dict, correct_parsed: dict, error_parsed: dict, mode: str):
        error_positions = [pos for pos, _, _ in self.injected_error_bytes]

        self._draw_frame(self.current_canvas, current_parsed, is_correct=True, show_stuffing=True)
        self._draw_frame(self.correct_canvas, correct_parsed, is_correct=True, show_stuffing=False)

        # Show/hide error frame based on show_error_frame flag
        if self.show_error_frame:
            self.error_label.pack(anchor="w")
            self.error_canvas.pack(fill="x", pady=2)
            self.error_text.pack(fill="x", pady=(0,6))

            if mode != "ok" or self.injected_error_bytes:
                self._draw_frame(self.error_canvas, error_parsed, is_correct=False,
                                 show_stuffing=False, error_positions=error_positions)
                self.error_label.config(text="❌ Ошибочный пакет (подсветка ошибок):")
            else:
                self._draw_frame(self.error_canvas, error_parsed, is_correct=True,
                                 show_stuffing=False)
                self.error_label.config(text="❌ Ошибочный пакет (ошибок нет):")
        else:
            self.error_label.pack_forget()
            self.error_canvas.pack_forget()
            self.error_text.pack_forget()

        crc_bits = self._get_crc_bits()
        crc_size = (crc_bits + 7) // 8

        self.current_text.delete("1.0","end")
        self.current_text.insert("end", f"Hex: {bytes_to_hex(self.last_frame)}\n")
        self.current_text.insert("end", f"Stuffed data: {bytes_to_hex(current_parsed.get('stuffed', b''))}\n")

        self.correct_text.delete("1.0","end")
        correct_fcs = int.from_bytes(correct_parsed.get('fcs', b''), 'big') if correct_parsed.get('fcs') else 0
        polynomial = self._get_polynomial()
        if polynomial is not None:
            correct_crc = compute_crc(correct_parsed.get('data', b''), polynomial, self.crc_type.get(), crc_bits)
        else:
            correct_crc = 0
        self.correct_text.insert("end", f"Length: {correct_parsed.get('length',0):02X} | Data: {bytes_to_hex(correct_parsed.get('data', b''))}\n")
        self.correct_text.insert("end", f"FCS: {correct_fcs:04X} | CRC: {correct_crc:0{crc_size*2}X}\n")

        if self.show_error_frame:
            self.error_text.delete("1.0","end")
            error_fcs = int.from_bytes(error_parsed.get('fcs', b''), 'big') if error_parsed.get('fcs') else 0
            error_crc_received = int.from_bytes(error_parsed.get('crc_received', b''), 'big') if error_parsed.get('crc_received') else 0
            self.error_text.insert("end", f"Length: {error_parsed.get('length',0):02X} | Data: {bytes_to_hex(error_parsed.get('data', b''))}\n")
            self.error_text.insert("end", f"FCS: {error_fcs:04X} | CRC received: {error_crc_received:0{crc_size*2}X}\n")

            if mode == "bad_crc":
                self.error_text.insert("end", f"\nERROR: Bad CRC - should be {correct_crc:0{crc_size*2}X}")
            elif mode == "bad_len":
                self.error_text.insert("end", f"\nERROR: Bad Length - should be {correct_parsed.get('length',0):02X}")
            elif self.injected_error_bytes:
                error_details = ", ".join([f"byte {pos}: 0x{old_val:02X}→0x{new_val:02X}"
                                           for pos, old_val, new_val in self.injected_error_bytes])
                self.error_text.insert("end", f"\nERROR: Manual errors: {error_details}")
            else:
                self.error_text.insert("end", f"\nNo errors injected")

    def _on_send(self, mode="ok"):
        raw = self._get_input_data()
        if raw is None:
            return

        polynomial = self._get_polynomial()
        if polynomial is None:
            return

        bad_crc = (mode == "bad_crc")
        bad_len = (mode == "bad_len")

        self.show_error_frame = (mode != "ok" or self.injected_error_bytes)

        block_length = self._get_block_length()
        if block_length is None:
            block_status = f"Auto ({len(raw)} bytes)"
        else:
            block_status = f"Fixed: {block_length} bytes"
        self.block_status_label.config(text=f"Block length: {block_status}")
        self._update_crc_settings_status()

        current_frame, current_values = self._build_frame(raw, bad_crc=False, bad_len=False, apply_errors=False)
        if current_frame is None:
            return

        correct_frame, correct_values = self._build_frame(raw, bad_crc=False, bad_len=False, apply_errors=False)
        error_frame, error_values = self._build_frame(raw, bad_crc=bad_crc, bad_len=bad_len, apply_errors=True)

        self.last_frame = error_frame if mode != "ok" else current_frame
        self.last_correct_frame = correct_frame

        current_parsed = self._parse_frame(current_frame)
        correct_parsed = self._parse_frame(correct_frame)
        error_parsed = self._parse_frame(error_frame)

        original_data = correct_parsed.get('data', b'')
        crc_bits = self._get_crc_bits()
        original_crc = compute_crc(original_data, polynomial, self.crc_type.get(), crc_bits)

        if mode != "ok" or self.injected_error_bytes:
            frame_to_check = error_parsed
            crc_valid, original_crc, received_crc = self._check_crc_correct_logic(error_parsed, original_crc)
        else:
            frame_to_check = current_parsed
            crc_valid, original_crc, received_crc = self._check_crc_correct_logic(current_parsed, original_crc)

        crc_size = (crc_bits + 7) // 8
        if crc_valid:
            self.crc_status_label.config(text=f"CRC: ✓ Valid (original 0x{original_crc:0{crc_size*2}X} = received 0x{received_crc:0{crc_size*2}X})",
                                         foreground="green")
        else:
            self.crc_status_label.config(text=f"CRC: ✗ Invalid (original 0x{original_crc:0{crc_size*2}X} ≠ received 0x{received_crc:0{crc_size*2}X})",
                                         foreground="red")

        self._draw_three_frame_comparison(current_parsed, correct_parsed, error_parsed, mode)

        if mode == "ok" and not self.injected_error_bytes:
            if self.corrected_positions:
                status = "Ошибки исправлены"
                color = "green"
            else:
                status = "Данные без ошибок"
                color = "green"
        else:
            if crc_valid:
                if self.injected_error_bytes:
                    status = "Ошибки внесены, но не обнаружены CRC"
                    color = "orange"
                    self._log(f"CRC НЕ ОБНАРУЖИЛ ошибки! Оригинальный CRC: 0x{original_crc:0{crc_size*2}X}, полученный CRC: 0x{received_crc:0{crc_size*2}X}")
                else:
                    status = "Данные без ошибок"
                    color = "green"
            else:
                if self.injected_error_bytes or mode != "ok":
                    status = "Ошибки обнаружены CRC"
                    color = "red"
                    self._log(f"CRC обнаружил ошибки! Оригинальный CRC: 0x{original_crc:0{crc_size*2}X}, полученный CRC: 0x{received_crc:0{crc_size*2}X}")
                else:
                    status = "Ошибки CRC"
                    color = "red"

        self.status_label.config(text=status, foreground=color)

        if mode != "ok" or self.injected_error_bytes:
            received_data = error_parsed.get('data', b'')
            self._log(f"=== ПРАВИЛЬНАЯ ПРОВЕРКА CRC ===")
            self._log(f"Оригинальные данные: {bytes_to_hex(original_data)}")
            self._log(f"Оригинальный CRC: 0x{original_crc:0{crc_size*2}X}")
            self._log(f"Полученные данные: {bytes_to_hex(received_data)}")
            self._log(f"Полученный CRC: 0x{received_crc:0{crc_size*2}X}")
            self._log(f"Результат проверки: {'VALID' if crc_valid else 'INVALID'}")
            self._log(f"Статус: {status}")

        if crc_valid:
            self._append_ops(f"Frame prepared. Status: {status}. CRC: Valid")
            self._log(f"CRC check: Valid")
        else:
            self._append_ops(f"Frame prepared. Status: {status}. CRC: Invalid")
            self._log(f"CRC check: Invalid")

        self._log(f"Prepared frame ({'OK' if mode=='ok' else 'ERR_MODE='+mode}): {bytes_to_hex(current_frame)}")

        mid = current_values.get('mid', b'')
        stuffed = current_values.get('stuffed', b'')
        self._log(f"Byte stuffing: {len(mid)} bytes -> {len(stuffed)} bytes (added {len(stuffed)-len(mid)} stuffing bytes)")
        self._append_ops(f"Byte stuffing: {len(mid)} bytes -> {len(stuffed)} bytes")

        frame_to_send = error_frame if mode != "ok" else current_frame
        self._send_frame(frame_to_send)

    def _send_frame(self, frame: bytes):
        mode = self.mode_var.get()
        try:
            if mode == "serial":
                if not SERIAL_AVAILABLE:
                    self._log("pyserial not available: cannot send over Serial")
                    return
                port = self.port_combo.get()
                if not port:
                    self._log("No COM port selected")
                    return
                baud = int(self.baud_combo.get())
                try:
                    with serial.Serial(port, baudrate=baud, timeout=0.2) as ser:
                        ser.write(frame)
                    self._log(f"✅ Sent over Serial {port}@{baud}")
                except Exception as e:
                    self._log(f"❌ Serial send error: {e}")
            else:
                host = self.host_entry.get().strip()
                if not host:
                    self._log("No UDP host specified")
                    return
                try:
                    port = int(self.port_entry.get().strip())
                except ValueError:
                    self._log("Invalid UDP port")
                    return
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(frame, (host, port))
                sock.close()
                self._log(f"✅ Sent over UDP to {host}:{port}")
        except Exception as e:
            self._log(f"❌ Send error: {e}")

    def _prepare_division(self):
        raw = self._get_input_data()
        if raw is None:
            return

        polynomial = self._get_polynomial()
        if polynomial is None:
            return

        crc_type = self.crc_type.get()
        crc_bits = self._get_crc_bits()
        crc_val, steps, dividend, final_bits = compute_crc_division(raw, polynomial, crc_type, crc_bits)
        self.division_steps = steps
        self.dividend_bits = dividend
        self.final_bits = final_bits
        self.current_step = 0
        self._reset_division_canvas()
        crc_size = (crc_bits + 7) // 8

        self._append_ops(f"Prepared {len(steps)} subtraction steps")
        self._append_ops(f"Data: {bytes_to_hex(raw)}")
        self._append_ops(f"Polynomial: 0x{polynomial:0{max(2, (crc_bits+7)//8*2)}X}")
        self._append_ops(f"Expected CRC: 0x{crc_val:0{crc_size*2}X}")

        self._draw_dividend_header(dividend)
        self._append_internal(f"Dividend bits: {dividend}")
        self._append_internal(f"Polynomial bits: {format(polynomial, f'0{crc_bits + 1}b')}")
        self._append_internal(f"Expected final bits: {final_bits}")

    def _prepare_error_division(self):
        raw = self._get_input_data()
        if raw is None:
            return

        polynomial = self._get_polynomial()
        if polynomial is None:
            return

        error_data = self._apply_errors_to_data(raw)
        if not error_data:
            error_data = raw

        crc_type = self.crc_type.get()
        crc_bits = self._get_crc_bits()
        crc_val, steps, dividend, final_bits = compute_crc_division(error_data, polynomial, crc_type, crc_bits)
        self.error_division_steps = steps
        self.error_dividend_bits = dividend
        self.error_final_bits = final_bits
        self.error_current_step = 0
        self._reset_error_division_canvas()
        crc_size = (crc_bits + 7) // 8

        self._append_ops(f"Prepared {len(steps)} error subtraction steps")
        self._append_ops(f"Error data: {bytes_to_hex(error_data)}")
        self._append_ops(f"Polynomial: 0x{polynomial:0{max(2, (crc_bits+7)//8*2)}X}")
        self._append_ops(f"Expected CRC: 0x{crc_val:0{crc_size*2}X}")

        self._draw_error_dividend_header(dividend)
        self._append_internal(f"Error dividend bits: {dividend}")
        self._append_internal(f"Polynomial bits: {format(polynomial, f'0{crc_bits + 1}b')}")
        self._append_internal(f"Expected final bits: {final_bits}")

    def _draw_dividend_header(self, dividend_bits):
        c = self.division_canvas
        y = self.division_y
        x = self.left_margin
        c.create_text(x, y, anchor="nw", text="Dividend (data + zeros):", font=("TkDefaultFont", 10, "bold"))
        c.create_text(x + 220, y, anchor="nw", text=dividend_bits, font=("Courier", 10), fill="blue")
        self.division_y += self.line_height * 2
        c.configure(scrollregion=c.bbox("all"))

    def _draw_error_dividend_header(self, dividend_bits):
        c = self.error_division_canvas
        y = self.error_division_y
        x = self.left_margin
        c.create_text(x, y, anchor="nw", text="Dividend (error data + zeros):", font=("TkDefaultFont", 10, "bold"))
        c.create_text(x + 250, y, anchor="nw", text=dividend_bits, font=("Courier", 10), fill="red")
        self.error_division_y += self.line_height * 2
        c.configure(scrollregion=c.bbox("all"))

    def _reset_division_canvas(self):
        self.division_canvas.delete("all")
        self.division_y = self.top_margin
        self.division_canvas.configure(scrollregion=(0,0,0,0))

    def _reset_error_division_canvas(self):
        self.error_division_canvas.delete("all")
        self.error_division_y = self.top_margin
        self.error_division_canvas.configure(scrollregion=(0,0,0,0))

    def _append_ops(self, txt):
        self.steps_text.config(state="normal")
        self.steps_text.insert("end", f"{txt}\n")
        self.steps_text.see("end")
        self.steps_text.config(state="disabled")

    def _append_internal(self, txt):
        self.internal_text.config(state="normal")
        self.internal_text.insert("end", f"{txt}\n")
        self.internal_text.see("end")
        self.internal_text.config(state="disabled")

    def _draw_ladder_step_persistent(self, step):
        c = self.division_canvas
        pos = step['position']
        current_bits = step['current_bits']
        poly_bits = step['poly_bits']
        result_bits = step['result_bits']

        x_base = self.left_margin + 220
        x_offset = x_base + pos * self.bit_w
        y = self.division_y

        c.create_text(self.left_margin, y, anchor="nw", text=f"pos {pos}", font=("TkDefaultFont",9,"italic"))
        c.create_text(x_offset, y, anchor="nw", text=current_bits, font=("Courier", 11), fill="black")
        y += self.line_height
        c.create_text(x_offset, y, anchor="nw", text=poly_bits, font=("Courier", 11), fill="red")
        y += self.line_height
        line_x1 = x_offset
        line_x2 = x_offset + max(len(poly_bits), len(result_bits)) * self.bit_w
        c.create_line(line_x1, y, line_x2, y, fill="#222", width=1)
        y += 6
        c.create_text(x_offset, y, anchor="nw", text=result_bits, font=("Courier", 11), fill="green")
        self.division_y = y + self.line_height
        c.configure(scrollregion=c.bbox("all"))
        try:
            c.yview_moveto(1.0)
            total_w = max(c.bbox("all")[2] if c.bbox("all") else 0, 1)
            canvas_width = c.winfo_width() or 800
            target_x = max(0, x_offset - 60)
            c.xview_moveto(target_x / total_w)
        except Exception:
            pass

    def _draw_error_ladder_step_persistent(self, step):
        c = self.error_division_canvas
        pos = step['position']
        current_bits = step['current_bits']
        poly_bits = step['poly_bits']
        result_bits = step['result_bits']

        x_base = self.left_margin + 250
        x_offset = x_base + pos * self.bit_w
        y = self.error_division_y

        c.create_text(self.left_margin, y, anchor="nw", text=f"pos {pos}", font=("TkDefaultFont",9,"italic"))
        c.create_text(x_offset, y, anchor="nw", text=current_bits, font=("Courier", 11), fill="black")
        y += self.line_height
        c.create_text(x_offset, y, anchor="nw", text=poly_bits, font=("Courier", 11), fill="red")
        y += self.line_height
        line_x1 = x_offset
        line_x2 = x_offset + max(len(poly_bits), len(result_bits)) * self.bit_w
        c.create_line(line_x1, y, line_x2, y, fill="#222", width=1)
        y += 6
        c.create_text(x_offset, y, anchor="nw", text=result_bits, font=("Courier", 11), fill="green")
        self.error_division_y = y + self.line_height
        c.configure(scrollregion=c.bbox("all"))
        try:
            c.yview_moveto(1.0)
            total_w = max(c.bbox("all")[2] if c.bbox("all") else 0, 1)
            canvas_width = c.winfo_width() or 800
            target_x = max(0, x_offset - 60)
            c.xview_moveto(target_x / total_w)
        except Exception:
            pass

    def _show_remainder(self, canvas, final_bits, dividend_bits, y_pos, is_error=False):
        crc_bits = self._get_crc_bits()
        remainder = final_bits[-crc_bits:] if crc_bits > 0 else ''
        crc_value = int(remainder, 2) if remainder else 0
        crc_size = (crc_bits + 7) // 8

        color = "darkred" if is_error else "darkgreen"
        label = "Error Remainder (CRC):" if is_error else "Remainder (CRC):"

        canvas.create_text(self.left_margin, y_pos, anchor="nw", text=label,
                           font=("TkDefaultFont", 10, "bold"), fill=color)
        canvas.create_text(self.left_margin + 180, y_pos, anchor="nw", text=remainder,
                           font=("Courier", 11), fill=color)
        y_pos += self.line_height
        canvas.create_text(self.left_margin, y_pos, anchor="nw",
                           text=f"CRC значение: 0x{crc_value:0{crc_size*2}X}",
                           font=("TkDefaultFont", 10, "bold"), fill=color)
        y_pos += self.line_height

        canvas.create_text(self.left_margin, y_pos, anchor="nw", text="Final bits:",
                           font=("TkDefaultFont", 9, "bold"))
        canvas.create_text(self.left_margin + 80, y_pos, anchor="nw", text=final_bits,
                           font=("Courier", 9), fill="purple")

        return y_pos + self.line_height * 2

    def _start_animation(self):
        if not self.division_steps:
            self._prepare_division()
            if not self.division_steps:
                return
        if self.current_step >= len(self.division_steps):
            self._reset_division_canvas()
            self._draw_dividend_header(self.dividend_bits)
            self.current_step = 0
        if not self.animating:
            self.animating = True
            self._log("Correct CRC animation started")
            self._schedule_next_step()

    def _start_error_animation(self):
        if not self.error_division_steps:
            self._prepare_error_division()
            if not self.error_division_steps:
                return
        if self.error_current_step >= len(self.error_division_steps):
            self._reset_error_division_canvas()
            self._draw_error_dividend_header(self.error_dividend_bits)
            self.error_current_step = 0
        if not self.error_animating:
            self.error_animating = True
            self._log("Error CRC animation started")
            self._schedule_next_error_step()

    def _schedule_next_step(self):
        if not self.animating:
            return
        delay = max(0.01, float(self.speed_scale.get()))
        self.anim_after = self.root.after(int(delay * 1000), self._animate_step)

    def _schedule_next_error_step(self):
        if not self.error_animating:
            return
        delay = max(0.01, float(self.speed_scale.get()))
        self.error_anim_after = self.root.after(int(delay * 1000), self._animate_error_step)

    def _animate_step(self):
        if self.current_step >= len(self.division_steps):
            self.animating = False
            final_y = self._show_remainder(self.division_canvas, self.final_bits, self.dividend_bits, self.division_y)
            self.division_y = final_y
            self.division_canvas.configure(scrollregion=self.division_canvas.bbox("all"))

            crc_bits = self._get_crc_bits()
            remainder = self.final_bits[-crc_bits:] if crc_bits > 0 else ''
            crc_value = int(remainder, 2) if remainder else 0
            crc_size = (crc_bits + 7) // 8

            self._append_ops(f"Correct CRC animation finished. Remainder: {remainder} = 0x{crc_value:0{crc_size*2}X}")
            self._log(f"Correct CRC animation finished. CRC: 0x{crc_value:0{crc_size*2}X}")
            return

        step = self.division_steps[self.current_step]
        self._draw_ladder_step_persistent(step)
        self._append_ops(f"Correct Step {self.current_step}: pos {step['position']} -> {step['current_bits']} XOR {step['poly_bits']} = {step['result_bits']}")
        self._append_internal(f"Correct Step internal: pos {step['position']} | current={step['current_bits']} | poly={step['poly_bits']} | result={step['result_bits']}")
        self.current_step += 1
        if self.animating:
            self._schedule_next_step()

    def _animate_error_step(self):
        if self.error_current_step >= len(self.error_division_steps):
            self.error_animating = False
            final_y = self._show_remainder(self.error_division_canvas, self.error_final_bits, self.error_dividend_bits, self.error_division_y, True)
            self.error_division_y = final_y
            self.error_division_canvas.configure(scrollregion=self.error_division_canvas.bbox("all"))

            crc_bits = self._get_crc_bits()
            remainder = self.error_final_bits[-crc_bits:] if crc_bits > 0 else ''
            crc_value = int(remainder, 2) if remainder else 0
            crc_size = (crc_bits + 7) // 8

            self._append_ops(f"Error CRC animation finished. Remainder: {remainder} = 0x{crc_value:0{crc_size*2}X}")
            self._log(f"Error CRC animation finished. CRC: 0x{crc_value:0{crc_size*2}X}")
            return

        step = self.error_division_steps[self.error_current_step]
        self._draw_error_ladder_step_persistent(step)
        self._append_ops(f"Error Step {self.error_current_step}: pos {step['position']} -> {step['current_bits']} XOR {step['poly_bits']} = {step['result_bits']}")
        self._append_internal(f"Error Step internal: pos {step['position']} | current={step['current_bits']} | poly={step['poly_bits']} | result={step['result_bits']}")
        self.error_current_step += 1
        if self.error_animating:
            self._schedule_next_error_step()

    def _pause_animation(self):
        if self.animating:
            self.animating = False
            if self.anim_after:
                try:
                    self.root.after_cancel(self.anim_after)
                except Exception:
                    pass
                self.anim_after = None
            self._log("Correct CRC animation paused")
            self._append_ops("Correct CRC animation paused.")

    def _pause_error_animation(self):
        if self.error_animating:
            self.error_animating = False
            if self.error_anim_after:
                try:
                    self.root.after_cancel(self.error_anim_after)
                except Exception:
                    pass
                self.error_anim_after = None
            self._log("Error CRC animation paused")
            self._append_ops("Error CRC animation paused.")

    def _next_division_step(self):
        if not self.division_steps:
            self._prepare_division()
            if not self.division_steps:
                return

        if self.current_step >= len(self.division_steps):
            final_y = self._show_remainder(self.division_canvas, self.final_bits, self.dividend_bits, self.division_y)
            self.division_y = final_y
            self.division_canvas.configure(scrollregion=self.division_canvas.bbox("all"))

            crc_bits = self._get_crc_bits()
            remainder = self.final_bits[-crc_bits:] if crc_bits > 0 else ''
            crc_value = int(remainder, 2) if remainder else 0
            crc_size = (crc_bits + 7) // 8

            self._append_ops(f"Division complete. Remainder: {remainder} = 0x{crc_value:0{crc_size*2}X}")
            return

        step = self.division_steps[self.current_step]
        self._draw_ladder_step_persistent(step)
        self._append_ops(f"Correct Step {self.current_step}: pos {step['position']} -> {step['current_bits']} XOR {step['poly_bits']} = {step['result_bits']}")
        self._append_internal(f"Correct Step internal: pos {step['position']} | current={step['current_bits']} | poly={step['poly_bits']} | result={step['result_bits']}")
        self.current_step += 1

    def _next_error_division_step(self):
        if not self.error_division_steps:
            self._prepare_error_division()
            if not self.error_division_steps:
                return

        if self.error_current_step >= len(self.error_division_steps):
            final_y = self._show_remainder(self.error_division_canvas, self.error_final_bits, self.error_dividend_bits, self.error_division_y, True)
            self.error_division_y = final_y
            self.error_division_canvas.configure(scrollregion=self.error_division_canvas.bbox("all"))

            crc_bits = self._get_crc_bits()
            remainder = self.error_final_bits[-crc_bits:] if crc_bits > 0 else ''
            crc_value = int(remainder, 2) if remainder else 0
            crc_size = (crc_bits + 7) // 8

            self._append_ops(f"Error division complete. Remainder: {remainder} = 0x{crc_value:0{crc_size*2}X}")
            return

        step = self.error_division_steps[self.error_current_step]
        self._draw_error_ladder_step_persistent(step)
        self._append_ops(f"Error Step {self.error_current_step}: pos {step['position']} -> {step['current_bits']} XOR {step['poly_bits']} = {step['result_bits']}")
        self._append_internal(f"Error Step internal: pos {step['position']} | current={step['current_bits']} | poly={step['poly_bits']} | result={step['result_bits']}")
        self.error_current_step += 1

    def _reset_division_steps(self):
        if self.animating:
            self._pause_animation()
        self.division_steps = []
        self.current_step = 0
        self.dividend_bits = ""
        self.final_bits = ""
        self.division_canvas.delete("all")
        self.division_y = self.top_margin
        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0","end")
        self.steps_text.insert("1.0", "Correct division steps reset.\n")
        self.steps_text.config(state="disabled")
        self.internal_text.config(state="normal")
        self.internal_text.delete("1.0","end")
        self.internal_text.insert("1.0", "Internal log reset.\n")
        self.internal_text.config(state="disabled")
        self._log("Correct division reset")
        self.injected_error_bytes = []
        self.corrected_positions = []

    def _reset_error_division_steps(self):
        if self.error_animating:
            self._pause_error_animation()
        self.error_division_steps = []
        self.error_current_step = 0
        self.error_dividend_bits = ""
        self.error_final_bits = ""
        self.error_division_canvas.delete("all")
        self.error_division_y = self.top_margin
        self.steps_text.config(state="normal")
        self.steps_text.delete("1.0","end")
        self.steps_text.insert("1.0", "Error division steps reset.\n")
        self.steps_text.config(state="disabled")
        self.internal_text.config(state="normal")
        self.internal_text.delete("1.0","end")
        self.internal_text.insert("1.0", "Internal log reset.\n")
        self.internal_text.config(state="disabled")
        self._log("Error division reset")

def main():
    root = tk.Tk()
    app = SenderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()