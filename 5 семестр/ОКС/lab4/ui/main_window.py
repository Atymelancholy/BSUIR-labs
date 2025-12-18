import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMessageBox, QGroupBox, QSlider, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.network import TokenRingNetwork
from ui.ring_canvas import RingCanvas
from ui.control_panel import ControlPanel
from ui.info_panel import InfoPanel
from ui.styles import AppStyles

class TokenRingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timeout_counter = 5.0

        self.setup_ui()

        self.network = TokenRingNetwork(
            num_stations=4,
            log_callback=self.log_message,
            timeout_reset_callback=self.reset_timeout_counter
        )

        self.control_panel.network = self.network
        self.info_panel.network = self.network
        self.canvas.network = self.network

        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.on_simulation_tick)
        self.simulation_timer.setInterval(500)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(50)

        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout_tick)
        self.timeout_timer.setInterval(100)

        self.update_display()

    def setup_ui(self):
        self.setWindowTitle("🌸 Token Ring Network Simulator")
        self.setGeometry(100, 100, 1800, 1000)

        self.setStyleSheet(AppStyles.get_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)

        left_widget = QWidget()
        left_layout = QHBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.control_panel = ControlPanel(None, self)
        self.control_panel.setMinimumWidth(400)
        self.control_panel.setMaximumWidth(450)
        left_layout.addWidget(self.control_panel, stretch=1)

        self.info_panel = InfoPanel(None, self)
        self.info_panel.setMinimumWidth(400)
        self.info_panel.setMaximumWidth(450)
        left_layout.addWidget(self.info_panel, stretch=1)

        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, stretch=2)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)

        simulation_control = self._create_simulation_control_panel()
        right_layout.addWidget(simulation_control)

        self.canvas = RingCanvas(None)
        self.canvas.setMinimumHeight(500)
        right_layout.addWidget(self.canvas, stretch=3)

        speed_control = self._create_speed_panel()
        right_layout.addWidget(speed_control)

        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, stretch=2)

    def _create_simulation_control_panel(self):
        group = QGroupBox("🚀 Управление симуляцией")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #FFFFFF;
                border: 2px solid #9B87F5;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 10px;
                font-weight: bold;
                color: #2D3436;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: #FFFFFF;
                color: #9B87F5;
                font-size: 12px;
            }
        """)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.start_btn_main = QPushButton("▶ Запустить симуляцию")
        self.start_btn_main.setStyleSheet("""
            QPushButton {
                background-color: #f3d8ce;
                color: #2D3436;
                border: none;
                border-radius: 8px;
                padding: 12px 8px;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #f3d8ce;
                opacity: 0.9;
            }
            QPushButton:pressed {
                background-color: #f3d8ce;
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #DFE6E9;
                color: #636E72;
            }
        """)
        self.start_btn_main.clicked.connect(self.start_simulation)

        self.stop_btn_main = QPushButton("⏸ Остановить симуляцию")
        self.stop_btn_main.setStyleSheet("""
            QPushButton {
                background-color: #9B87F5;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px 8px;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #9B87F5;
                opacity: 0.9;
            }
            QPushButton:pressed {
                background-color: #9B87F5;
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #DFE6E9;
                color: #636E72;
            }
        """)
        self.stop_btn_main.clicked.connect(self.stop_simulation)
        self.stop_btn_main.setEnabled(False)

        self.reset_btn_main = QPushButton("🔄 Сбросить сеть")
        self.reset_btn_main.setStyleSheet("""
            QPushButton {
                background-color: #A8D5BA;
                color: #2D3436;
                border: none;
                border-radius: 8px;
                padding: 12px 8px;
                font-weight: bold;
                font-size: 11px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #A8D5BA;
                opacity: 0.9;
            }
            QPushButton:pressed {
                background-color: #A8D5BA;
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #DFE6E9;
                color: #636E72;
            }
        """)
        self.reset_btn_main.clicked.connect(self.reset_network)

        layout.addWidget(self.start_btn_main)
        layout.addWidget(self.stop_btn_main)
        layout.addWidget(self.reset_btn_main)

        group.setLayout(layout)
        return group

    def _create_speed_panel(self):
        group = QGroupBox("⚡ Управление скоростью симуляции")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #FFFFFF;
                border: 2px solid #9B87F5;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 10px;
                font-weight: bold;
                color: #2D3436;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: #FFFFFF;
                color: #9B87F5;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)

        slider_layout = QVBoxLayout()

        self.speed_label = QLabel("Текущая скорость: Средняя (x1.0)")
        self.speed_label.setStyleSheet("""
            QLabel {
                color: #9B87F5; 
                font-weight: bold; 
                font-size: 13px;
                padding: 5px;
                background-color: #FDF6F3;
                border-radius: 6px;
                text-align: center;
            }
        """)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider_layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.valueChanged.connect(self.change_simulation_speed)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #D4C1B8;
                height: 8px;
                background: #FFFFFF;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #A8D5BA;
                border: 2px solid #A8D5BA;
                width: 20px;
                margin: -8px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: #9B87F5;
                border: 2px solid #9B87F5;
            }
        """)
        slider_layout.addWidget(self.speed_slider)

        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("Медленно"))
        labels_layout.addStretch()
        labels_layout.addWidget(QLabel("⚡ Быстро"))
        slider_layout.addLayout(labels_layout)

        layout.addLayout(slider_layout)
        group.setLayout(layout)

        return group

    def change_simulation_speed(self, value):
        speed_factors = {
            1: 2.0,
            2: 1.5,
            3: 1.2,
            4: 1.0,
            5: 0.8,
            6: 0.6,
            7: 0.4,
            8: 0.3,
            9: 0.2,
            10: 0.1
        }

        speed_names = {
            1: "Очень медленно", 2: "Медленно", 3: "Немного медленно",
            4: "Средняя", 5: "Немного быстро", 6: "Быстро",
            7: "Очень быстро", 8: "Супер быстро", 9: "Ультра быстро", 10: "Максимальная"
        }

        factor = speed_factors.get(value, 1.0)
        speed_name = speed_names.get(value, "Средняя")

        if hasattr(self, 'simulation_timer'):
            self.simulation_timer.setInterval(int(500 * factor))
        if hasattr(self, 'animation_timer'):
            self.animation_timer.setInterval(int(50 * factor))

        self.speed_label.setText(f"Текущая скорость: {speed_name} (x{1/factor:.1f})")

    def start_simulation(self):
        if self.network.is_running:
            return

        self.network.start_simulation()

        if self.network.token_holder_id is not None:
            self.timeout_counter = 5.0
            self.simulation_timer.start()
            self.animation_timer.start()
            self.timeout_timer.start()
            self.control_panel.set_simulation_buttons_state(True)
            self._set_main_buttons_state(True)
            self.log_message("Симуляция запущена", "#A8D5BA")
        else:
            self.log_message("Не удалось запустить симуляцию", "#9B87F5")

    def stop_simulation(self):
        if not self.network.is_running:
            return

        self.network.stop_simulation()
        self.simulation_timer.stop()
        self.animation_timer.stop()
        self.timeout_timer.stop()

        self.timeout_counter = 5.0
        self.control_panel.set_simulation_buttons_state(False)
        self._set_main_buttons_state(False)
        self.log_message("⏸Симуляция остановлена", "#f3d8ce")

    def reset_network(self):
        self.stop_simulation()
        self.network.reset_network()
        self.control_panel.update_station_spinners()
        self.update_display()
        self.log_message("Сеть сброшена", "#A8D5BA")

    def _set_main_buttons_state(self, running: bool):
        self.start_btn_main.setEnabled(not running)
        self.stop_btn_main.setEnabled(running)

    def change_station_count(self, count: int):
        if not self.network.is_running:
            self.network = TokenRingNetwork(
                num_stations=count,
                log_callback=self.log_message,
                timeout_reset_callback=self.reset_timeout_counter
            )

            self.control_panel.network = self.network
            self.info_panel.network = self.network
            self.canvas.network = self.network

            self.control_panel.update_station_spinners()
            self.update_display()

            self.log_message(f"Создана новая сеть с {count} станциями", "#A8D5BA")

    def on_simulation_tick(self):
        if self.network.is_running:
            self.network.step_simulation()
            self.update_display()

    def on_timeout_tick(self):
        if self.network.is_running:
            self.timeout_counter -= 0.1

            if self.timeout_counter <= 0:
                if self.network._check_token_loss():
                    self.network._recover_token()
                self.timeout_counter = 5.0

            self.info_panel.update_timeout_display(self.timeout_counter, self.network.is_running)

    def update_animation(self):
        if self.network.is_running:
            self.canvas.update_animation()

    def update_display(self):
        self.canvas.update_animation()

        self.info_panel.update_token_info(self.network)

        self.info_panel.update_queues(self.network)

        self.info_panel.update_timeout_display(self.timeout_counter, self.network.is_running)

    def log_message(self, message: str, color: str = "#636E72"):
        if hasattr(self, 'info_panel') and self.info_panel is not None:
            self.info_panel.log_message(message, color)

    def reset_timeout_counter(self):
        if hasattr(self, 'network') and self.network.is_running:
            self.timeout_counter = 5.0

    def closeEvent(self, event):
        self.stop_simulation()
        event.accept()
