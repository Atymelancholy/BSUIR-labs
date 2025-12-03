from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QSpinBox, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ControlPanel(QWidget):
    def __init__(self, network, main_window):
        super().__init__()
        self.network = network
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(self._create_station_group())

        layout.addWidget(self._create_message_group())

        layout.addWidget(self._create_error_group())

        layout.addStretch()
        self.setLayout(layout)
        self.setMinimumWidth(380)

    def _create_station_group(self):
        group = QGroupBox("Конфигурация сети")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Количество станций:"))
        self.station_count_combo = QComboBox()
        for i in range(2, 11):
            self.station_count_combo.addItem(f"{i} станций", i)
        self.station_count_combo.setCurrentIndex(2)
        self.station_count_combo.currentIndexChanged.connect(self._on_station_count_changed)
        self._apply_standard_style(self.station_count_combo)
        layout.addWidget(self.station_count_combo)

        group.setLayout(layout)
        return group

    def _create_message_group(self):
        group = QGroupBox("Отправка сообщений")
        layout = QVBoxLayout()

        stations_layout = QHBoxLayout()

        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("От станции:"))
        self.source_combo = QComboBox()
        self._populate_station_combo(self.source_combo)
        self.source_combo.setCurrentIndex(0)
        self._apply_standard_style(self.source_combo)
        source_layout.addWidget(self.source_combo)
        stations_layout.addLayout(source_layout)

        dest_layout = QVBoxLayout()
        dest_layout.addWidget(QLabel("К станции:"))
        self.dest_combo = QComboBox()
        self._populate_station_combo(self.dest_combo)
        self.dest_combo.setCurrentIndex(1)
        self._apply_standard_style(self.dest_combo)
        dest_layout.addWidget(self.dest_combo)
        stations_layout.addLayout(dest_layout)

        layout.addLayout(stations_layout)

        message_layout = QVBoxLayout()
        message_layout.addWidget(QLabel("Текст сообщения:"))
        self.message_input = QLineEdit()
        self.message_input.setText("Привет, Token Ring!")
        self.message_input.setPlaceholderText("Введите текст сообщения...")
        self._apply_standard_style(self.message_input)
        message_layout.addWidget(self.message_input)
        layout.addLayout(message_layout)

        self.send_btn = self._create_button("Отправить сообщение", "#A8D5BA", self.send_message)
        layout.addWidget(self.send_btn)

        group.setLayout(layout)
        return group

    def _create_error_group(self):
        group = QGroupBox("Тестирование ошибок")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Целевая станция:"))
        self.error_station_combo = QComboBox()
        self._populate_station_combo(self.error_station_combo)
        self.error_station_combo.setCurrentIndex(0)
        self._apply_standard_style(self.error_station_combo)
        layout.addWidget(self.error_station_combo)

        buttons_layout = QVBoxLayout()

        self.damage_btn = self._create_button("Повредить станцию", "#9B87F5", self.damage_station)
        self.repair_btn = self._create_button("Восстановить станцию", "#A8D5BA", self.repair_station)
        self.error_btn = self._create_button("Имитировать ошибку", "#f3d8ce", self.introduce_error)

        buttons_layout.addWidget(self.damage_btn)
        buttons_layout.addWidget(self.repair_btn)
        buttons_layout.addWidget(self.error_btn)

        layout.addLayout(buttons_layout)

        group.setLayout(layout)
        return group

    def _populate_station_combo(self, combo_box):
        combo_box.clear()
        if self.network and hasattr(self.network, 'stations'):
            for i in range(len(self.network.stations)):
                combo_box.addItem(f"Станция {i}", i)
        else:
            for i in range(4):
                combo_box.addItem(f"Станция {i}", i)

    def _on_station_count_changed(self, index):
        if hasattr(self, 'station_count_combo'):
            count = self.station_count_combo.currentData()
            if count:
                self.main_window.change_station_count(count)

    def _create_button(self, text, color, callback):
        button = QPushButton(text)

        text_color = "#FFFFFF" if color in ["#9B87F5", "#A8D5BA"] else "#2D3436"

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 12px 8px;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {color};
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: {color};
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #DFE6E9;
                color: #636E72;
            }}
        """)
        button.clicked.connect(callback)
        return button

    def _apply_standard_style(self, widget):
        widget.setStyleSheet("""
            QComboBox, QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D4C1B8;
                border-radius: 6px;
                padding: 10px;
                color: #2D3436;
                font-size: 12px;
                min-height: 25px;
                margin: 2px;
            }
            QComboBox:hover, QLineEdit:hover {
                border: 1px solid #A8D5BA;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #9B87F5;
                background-color: #FDF6F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #A8D5BA;
                width: 0px;
                height: 0px;
            }
        """)

    def send_message(self):
        if self.network is None:
            QMessageBox.warning(self, "Ошибка", "Сеть не инициализирована")
            return

        source = self.source_combo.currentData()
        dest = self.dest_combo.currentData()
        message_text = self.message_input.text().strip()

        if source is None or dest is None:
            QMessageBox.warning(self, "Ошибка", "Неверный выбор станций")
            return

        if not message_text:
            QMessageBox.warning(self, "Ошибка", "Введите текст сообщения")
            return

        if source == dest:
            QMessageBox.warning(self, "Ошибка", "Станция не может отправить сообщение самой себе")
            return

        if source >= len(self.network.stations):
            QMessageBox.warning(self, "Ошибка", f"🚫 Станция {source} не существует")
            return

        if dest >= len(self.network.stations):
            QMessageBox.warning(self, "Ошибка", f"🚫 Станция {dest} не существует")
            return

        if hasattr(self.network.stations[source], 'state'):
            station_state = self.network.stations[source].state
            if str(station_state) == "StationState.DAMAGED" or "DAMAGED" in str(station_state):
                QMessageBox.warning(self, "Ошибка", f"🚫 Станция {source} повреждена и не может отправлять сообщения")
                return

        if hasattr(self.network.stations[dest], 'state'):
            station_state = self.network.stations[dest].state
            if str(station_state) == "StationState.DAMAGED" or "DAMAGED" in str(station_state):
                QMessageBox.warning(self, "Ошибка", f"🚫 Станция {dest} повреждена и не может принимать сообщения")
                return

        success = self.network.send_message(source, dest, message_text)
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось отправить сообщение")
        else:
            self.message_input.clear()

    def damage_station(self):
        if self.network is None:
            return

        station_id = self.error_station_combo.currentData()
        if station_id is None:
            return

        if station_id < len(self.network.stations):
            self.network.damage_station(station_id)
        else:
            QMessageBox.warning(self, "Ошибка", f"🚫 Станция {station_id} не существует")

    def repair_station(self):
        if self.network is None:
            return

        station_id = self.error_station_combo.currentData()
        if station_id is None:
            return

        if station_id < len(self.network.stations):
            self.network.repair_station(station_id)
        else:
            QMessageBox.warning(self, "Ошибка", f"🚫 Станция {station_id} не существует")

    def introduce_error(self):
        if self.network is None:
            return

        station_id = self.error_station_combo.currentData()
        if station_id is None:
            return

        if station_id < len(self.network.stations):
            self.network.introduce_error(station_id)
        else:
            QMessageBox.warning(self, "Ошибка", f"🚫 Станция {station_id} не существует")

    def update_station_spinners(self):
        if self.network and hasattr(self.network, 'stations') and self.network.stations:

            self._populate_station_combo(self.source_combo)
            self._populate_station_combo(self.dest_combo)
            self._populate_station_combo(self.error_station_combo)

            if self.source_combo.count() > 0:
                self.source_combo.setCurrentIndex(0)
            if self.dest_combo.count() > 1:
                self.dest_combo.setCurrentIndex(1)
            if self.error_station_combo.count() > 0:
                self.error_station_combo.setCurrentIndex(0)

    def set_simulation_buttons_state(self, running: bool):
        """Этот метод теперь не используется для кнопок управления симуляцией,
        но оставляем его для совместимости, если он вызывается из других мест"""
        pass