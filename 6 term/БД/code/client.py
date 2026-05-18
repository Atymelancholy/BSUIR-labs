import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font, scrolledtext
from typing import Dict, List, Optional, Any

import requests
from PIL import Image, ImageTk

BASE_URL = "http://localhost:8000/api"


class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.last_result = None

    def _request(self, method, endpoint, **kwargs):
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code >= 400:
                messagebox.showerror(f"Ошибка {response.status_code}", response.text)
                return None
            return response.json()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return None

    def get_tables(self):
        return self._request("GET", "tables")

    def get_table_schema(self, table_name):
        return self._request("GET", f"table/{table_name}/schema")

    def get_table_data(self, table_name, filters=None, limit=100, offset=0):
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        return self._request("GET", f"table/{table_name}", params=params)

    def get_record(self, table_name, record_id):
        return self._request("GET", f"table/{table_name}/{record_id}")

    def create_record(self, table_name, data):
        return self._request("POST", f"table/{table_name}", json=data)

    def update_record(self, table_name, record_id, data):
        return self._request("PUT", f"table/{table_name}/{record_id}", json=data)

    def delete_record(self, table_name, record_id):
        return self._request("DELETE", f"table/{table_name}/{record_id}")

    def list_queries(self):
        return self._request("GET", "queries")

    def execute_query(self, query_name):
        return self._request("GET", f"queries/{query_name}")

    def save_result(self, data, fmt="excel"):
        return self._request("POST", "save-result", json={"data": data, "file_format": fmt})

    def create_backup(self, password, table_name=None):
        return self._request("POST", "backup", json={"password": password, "table_name": table_name})


def setup_styles():
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    bg_color = "#fff0f5"
    fg_color = "#333333"
    select_color = "#ff99cc"
    entry_bg = "#ffffff"
    button_bg = "#ffe4e1"
    accent_color = "#ff69b4"
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Segoe UI", size=10)
    style.configure(".", background=bg_color, foreground=fg_color, font=default_font)
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TFrame", background=bg_color)
    style.configure("TButton", padding=6, relief="flat", background=button_bg, foreground=fg_color)
    style.map("TButton", background=[("active", "#ffccdd"), ("pressed", select_color)])
    style.configure("Accent.TButton", background=accent_color, foreground="white")
    style.map("Accent.TButton", background=[("active", "#ff1493")])
    style.configure("TCombobox", fieldbackground=entry_bg, background=entry_bg, foreground=fg_color,
                    arrowcolor=accent_color)
    style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color)
    style.configure("Treeview", background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
    style.map("Treeview", background=[("selected", select_color)])
    style.configure("Treeview.Heading", background="#ffe4e1", foreground=fg_color)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌸 Animal Shelter Manager - Berkeley DB (ЛР4)")
        self.geometry("1000x650")
        self.minsize(800, 500)
        setup_styles()
        self.api = APIClient()
        self.cat_logo = None
        self.current_table = None
        self.current_data = []
        self.current_filters = {}
        self.table_columns = []

        self.create_menu()
        self.create_header()
        self.create_toolbar()
        self.create_table()
        self.bind_hotkeys()
        self.load_databases_into_menu()

    def create_menu(self):
        menubar = tk.Menu(self, bg="#ffe4e1", fg="#333333",
                          activebackground="#ff99cc", activeforeground="white")

        file_menu = tk.Menu(menubar, tearoff=0, bg="#ffe4e1", fg="#333333",
                            activebackground="#ff99cc", activeforeground="white")
        file_menu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+E")
        menubar.add_cascade(label="File", menu=file_menu, underline=0)

        # Меню Databases (Alt+D) - для ЛР4
        self.databases_menu = tk.Menu(menubar, tearoff=0, bg="#ffe4e1", fg="#333333",
                                      activebackground="#ff99cc", activeforeground="white")
        menubar.add_cascade(label="Databases", menu=self.databases_menu, underline=0)

        operations_menu = tk.Menu(menubar, tearoff=0, bg="#ffe4e1", fg="#333333",
                                  activebackground="#ff99cc", activeforeground="white")
        operations_menu.add_command(label="Add", command=self.add_record, accelerator="Ctrl+A")
        operations_menu.add_command(label="View", command=self.view_record, accelerator="Ctrl+V")
        operations_menu.add_command(label="Update", command=self.update_record, accelerator="Ctrl+U")
        operations_menu.add_command(label="Delete", command=self.delete_record, accelerator="Ctrl+D")
        operations_menu.add_separator()
        operations_menu.add_command(label="Query", command=self.show_query_dialog, accelerator="Ctrl+Q")
        operations_menu.add_command(label="Save Result", command=self.save_result, accelerator="Ctrl+S")
        operations_menu.add_command(label="Backup", command=self.show_backup_dialog, accelerator="Ctrl+B")
        operations_menu.add_separator()
        # Кнопка конвертера в меню Operations
        operations_menu.add_command(
            label="Конвертировать PostgreSQL → Berkeley DB (ЛР3)",
            command=self.run_berkeley_converter,
            accelerator="Ctrl+R"
        )
        menubar.add_cascade(label="Operations", menu=operations_menu, underline=0)

        self.config(menu=menubar)

    def create_header(self):
        header_frame = ttk.Frame(self, padding="5")
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)
        header_frame.columnconfigure(2, weight=0)
        header_frame.columnconfigure(3, weight=1)

        try:
            pil_image = Image.open("1.png").resize((44, 64), Image.Resampling.LANCZOS)
            self.cat_logo = ImageTk.PhotoImage(pil_image)
            logo_label = ttk.Label(header_frame, image=self.cat_logo)
        except:
            logo_label = ttk.Label(header_frame, text="🐱", font=("Segoe UI", 32))
        logo_label.grid(row=0, column=1, padx=(0, 10))

        title_label = ttk.Label(header_frame, text="Animal Shelter Manager (Berkeley DB)",
                                font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=2, padx=(10, 10))

    def create_toolbar(self):
        frame = ttk.Frame(self, padding="8 5")
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="Filter field:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_field_combo = ttk.Combobox(frame, state="readonly", width=20)
        self.filter_field_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Value:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_value_entry = ttk.Entry(frame, width=25)
        self.filter_value_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(frame, text="Apply Filter", command=self.apply_filter, style="Accent.TButton").pack(side=tk.LEFT,
                                                                                                       padx=5)
        ttk.Button(frame, text="Clear Filter", command=self.clear_filter).pack(side=tk.LEFT, padx=5)

        # Кнопка конвертера на панели инструментов
        ttk.Button(
            frame,
            text="🔄 PostgreSQL → Berkeley DB",
            command=self.run_berkeley_converter,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=(24, 5))

    def create_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        self.tree = ttk.Treeview(frame, columns=(), show="headings",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                 selectmode="browse")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda e: self.view_record())

    def bind_hotkeys(self):
        self.bind_all("<Control-a>", lambda e: self.add_record())
        self.bind_all("<Control-v>", lambda e: self.view_record())
        self.bind_all("<Control-u>", lambda e: self.update_record())
        self.bind_all("<Control-d>", lambda e: self.delete_record())
        self.bind_all("<Control-q>", lambda e: self.show_query_dialog())
        self.bind_all("<Control-s>", lambda e: self.save_result())
        self.bind_all("<Control-b>", lambda e: self.show_backup_dialog())
        self.bind_all("<Control-r>", lambda e: self.run_berkeley_converter())  # Ctrl+R для конвертера
        self.bind_all("<Control-e>", lambda e: self.quit())

    def load_databases_into_menu(self):
        result = self.api.get_tables()
        if result and "tables" in result:
            tables = result["tables"]
        else:
            tables = ["Animal", "Aviary", "Employee", "Volunteer"]

        # Очищаем меню
        self.databases_menu.delete(0, tk.END)

        for table in tables:
            self.databases_menu.add_command(
                label=table,
                command=lambda t=table: self.switch_database(t)
            )

    def switch_database(self, table_name):
        self.current_table = table_name
        self.current_filters = {}
        self.filter_value_entry.delete(0, tk.END)
        self.load_table_data()

        schema = self.api.get_table_schema(table_name)
        if schema and "columns" in schema:
            self.table_columns = [col["column_name"] for col in schema["columns"]]
            self.filter_field_combo["values"] = self.table_columns
            if self.table_columns:
                self.filter_field_combo.current(0)

    def load_table_data(self):
        if not self.current_table:
            return

        result = self.api.get_table_data(self.current_table, filters=self.current_filters, limit=500)
        if result and "data" in result:
            self.current_data = result["data"]
            self.display_data(self.current_data)
            self.api.last_result = self.current_data

    def display_data(self, data):
        self.tree.delete(*self.tree.get_children())
        if not data:
            return

        columns = list(data[0].keys())
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.W)
            self.tree.column(col, width=120, minwidth=70, anchor=tk.W)

        for row in data:
            self.tree.insert("", tk.END, values=[row.get(col, "") for col in columns])

    def apply_filter(self):
        field = self.filter_field_combo.get()
        value = self.filter_value_entry.get().strip()
        if not field or not value:
            messagebox.showwarning("Фильтр", "Выберите поле и введите значение")
            return
        self.current_filters = {field: value}
        self.load_table_data()

    def clear_filter(self):
        self.current_filters = {}
        self.filter_value_entry.delete(0, tk.END)
        self.load_table_data()

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите запись в таблице")
            return None
        item = self.tree.item(selection[0])
        columns = self.tree["columns"]
        if "id" in columns:
            return item["values"][columns.index("id")]
        return item["values"][0]

    def add_record(self):
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Сначала выберите базу данных")
            return
        schema = self.api.get_table_schema(self.current_table)
        if not schema or "columns" not in schema:
            return
        dialog = AddEditDialog(self, "Добавить запись", schema["columns"], mode="add")
        self.wait_window(dialog)
        if dialog.result:
            self.api.create_record(self.current_table, dialog.result)
            self.load_table_data()

    def view_record(self):
        if not self.current_table or not (record_id := self.get_selected_id()):
            return
        record = self.api.get_record(self.current_table, record_id)
        if record and (schema := self.api.get_table_schema(self.current_table)):
            ViewDialog(self, "Просмотр записи", schema["columns"], record)

    def update_record(self):
        if not self.current_table or not (record_id := self.get_selected_id()):
            return
        record = self.api.get_record(self.current_table, record_id)
        schema = self.api.get_table_schema(self.current_table)
        if not record or not schema:
            return
        dialog = AddEditDialog(self, "Обновить запись", schema["columns"], mode="edit", initial=record)
        self.wait_window(dialog)
        if dialog.result:
            self.api.update_record(self.current_table, record_id, dialog.result)
            self.load_table_data()

    def delete_record(self):
        if not self.current_table or not (record_id := self.get_selected_id()):
            return
        if messagebox.askyesno("Удаление", f"Удалить запись с ID {record_id}?"):
            self.api.delete_record(self.current_table, record_id)
            self.load_table_data()

    def show_query_dialog(self):
        queries = self.api.list_queries()
        if not queries or "queries" not in queries:
            return
        dialog = QueryDialog(self, queries["queries"])
        self.wait_window(dialog)
        if dialog.result:
            result = self.api.execute_query(dialog.result)
            if result and "data" in result:
                self.current_data = result["data"]
                self.display_data(self.current_data)
                self.api.last_result = self.current_data
                self.current_table = None

    def save_result(self):
        if self.api.last_result is None:
            messagebox.showwarning("Сохранение", "Нет данных для сохранения")
            return
        fmt = simpledialog.askstring("Формат", "Введите формат (csv или excel):", initialvalue="excel")
        if fmt not in ("csv", "excel"):
            messagebox.showerror("Ошибка", "Формат должен быть csv или excel")
            return
        result = self.api.save_result(self.api.last_result, fmt)
        if result and "filepath" in result:
            messagebox.showinfo("Сохранение", f"Файл сохранён:\n{result['filepath']}")

    def show_backup_dialog(self):
        password = simpledialog.askstring("Бэкап", "Введите пароль суперпользователя:", show="*")
        if password is None:
            return
        table = None
        if not messagebox.askyesno("Бэкап", "Создать бэкап всей БД? (Нет - выберите таблицу)"):
            table = simpledialog.askstring("Бэкап", "Введите имя таблицы:")
        result = self.api.create_backup(password, table)
        if result and "filepath" in result:
            messagebox.showinfo("Бэкап", f"Бэкап создан:\n{result['filepath']}")

    def _show_converter_log(self, text: str, title: str = "Вывод converter.py"):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("900x520")
        txt = scrolledtext.ScrolledText(win, width=100, height=28, wrap="word", font=("Consolas", 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        ttk.Button(win, text="Закрыть", command=win.destroy).pack(pady=6)

    def run_berkeley_converter(self):
        """Запускает конвертер PostgreSQL → Berkeley DB (ЛР3) тихо"""
        import subprocess
        import sys
        import os

        project_root = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(project_root, "converter.py")

        if os.path.isfile(script):
            subprocess.Popen(
                [sys.executable, script],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
class AddEditDialog(tk.Toplevel):
    def __init__(self, parent, title, columns, mode="add", initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x500")
        self.minsize(400, 300)
        self.configure(bg="#fff0f5")
        self.columns = columns
        self.mode = mode
        self.initial = initial or {}
        self.result = None
        self.entries = {}
        self.create_widgets()
        self.set_initial()
        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        self.grab_set()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0, bg="#fff0f5")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0
        for col in self.columns:
            col_name = col["column_name"]
            if col_name == "id" and self.mode == "add":
                continue
            ttk.Label(scrollable_frame, text=col_name, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, pady=5, padx=5)
            entry = ttk.Entry(scrollable_frame, width=40)
            entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
            self.entries[col_name] = entry
            row += 1

        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="OK", command=self.ok, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

    def set_initial(self):
        for key, entry in self.entries.items():
            if key in self.initial:
                entry.insert(0, str(self.initial[key]))

    def ok(self):
        data = {}
        for col in self.columns:
            col_name = col["column_name"]
            if col_name == "id" and self.mode == "add":
                continue
            entry = self.entries.get(col_name)
            if not entry:
                continue
            val = entry.get().strip()
            if val == "":
                data[col_name] = None
            else:
                data[col_name] = val
        self.result = data
        self.destroy()

    def cancel(self):
        self.destroy()


class ViewDialog(tk.Toplevel):
    def __init__(self, parent, title, columns, record):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x500")
        self.minsize(400, 300)
        self.configure(bg="#fff0f5")
        self.create_widgets(columns, record)
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()

    def create_widgets(self, columns, record):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0, bg="#fff0f5")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0
        for col in columns:
            col_name = col["column_name"]
            ttk.Label(scrollable_frame, text=col_name, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, pady=5, padx=5)
            value = record.get(col_name, "")
            ttk.Label(scrollable_frame, text=str(value), background="#ffffff", foreground="#333333",
                      relief="sunken", padding=3).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
            row += 1
        ttk.Button(scrollable_frame, text="OK", command=self.destroy, style="Accent.TButton").grid(
            row=row, column=0, columnspan=2, pady=15)


class QueryDialog(tk.Toplevel):
    def __init__(self, parent, queries):
        super().__init__(parent)
        self.title("Выберите специальный запрос")
        self.geometry("600x400")
        self.minsize(500, 300)
        self.configure(bg="#fff0f5")
        self.queries = queries
        self.result = None

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="Доступные запросы:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=5)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  font=("Segoe UI", 10), bg="#ffffff", fg="#333333",
                                  selectbackground="#ff99cc", selectforeground="white")
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for q in queries:
            self.listbox.insert(tk.END, f"{q['name']}: {q['description']}")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Выполнить", command=self.ok, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.listbox.bind("<Double-1>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())
        self.grab_set()

    def ok(self):
        selection = self.listbox.curselection()
        if selection:
            self.result = self.listbox.get(selection[0]).split(":", 1)[0].strip()
        self.destroy()

    def cancel(self):
        self.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()