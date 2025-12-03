from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QListWidget, QTextEdit, QPushButton
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from core.station import StationState

class InfoPanel(QWidget):
    def __init__(self, network, main_window):
        super().__init__()
        self.network = network
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(self._create_timeout_group())

        layout.addWidget(self._create_token_group())

        layout.addWidget(self._create_queue_group())

        layout.addWidget(self._create_log_group())

        layout.addStretch()
        self.setLayout(layout)
        self.setMinimumWidth(380)

    def _create_timeout_group(self):
        group = QGroupBox("Таймер тайм-аута")
        layout = QVBoxLayout()

        self.timeout_label = QLabel("Осталось: 5.0 сек")
        self.timeout_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.timeout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeout_label.setStyleSheet("""
            QLabel {
                background-color: #A8D5BA;
                color: #2D3436;
                padding: 12px;
                border-radius: 10px;
                font-weight: bold;
                border: 2px solid #9B87F5;
            }
        """)
        layout.addWidget(self.timeout_label)

        group.setLayout(layout)
        return group

    def _create_token_group(self):
        group = QGroupBox("Информация о токене")
        layout = QVBoxLayout()

        self.token_status_label = QLabel("Владелец: не назначен")
        self.token_status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.token_status_label.setStyleSheet("""
            QLabel {
                background-color: #FDF6F3;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #D4C1B8;
                color: #2D3436;
            }
        """)
        self.token_status_label.setWordWrap(True)
        layout.addWidget(self.token_status_label)

        group.setLayout(layout)
        return group

    def _create_queue_group(self):
        group = QGroupBox("Очереди сообщений")
        layout = QVBoxLayout()

        self.queue_list = QListWidget()
        self.queue_list.setFont(QFont("Consolas", 9))
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #D4C1B8;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #E8D5CC;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        layout.addWidget(self.queue_list)

        group.setLayout(layout)
        return group

    def _create_log_group(self):
        group = QGroupBox("Журнал событий")
        layout = QVBoxLayout()

        log_controls_layout = QVBoxLayout()

        clear_btn = QPushButton("Очистить журнал")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #A8D5BA;
                color: #2D3436;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #9B87F5;
                color: white;
            }
        """)
        clear_btn.clicked.connect(self.clear_log)
        log_controls_layout.addWidget(clear_btn)

        layout.addLayout(log_controls_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(300)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                color: #2D3436;
                border: 1px solid #D4C1B8;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def clear_log(self):
        self.log_text.clear()

    def update_timeout_display(self, timeout_counter: float, is_running: bool):
        if is_running:
            if timeout_counter > 0:
                self.timeout_label.setText(f"Осталось: {timeout_counter:.1f} сек")

                if timeout_counter < 1.0:
                    style = """
                        QLabel {
                            background-color: #9B87F5;
                            color: white;
                            padding: 12px;
                            border-radius: 10px;
                            font-weight: bold;
                            border: 2px solid #A8D5BA;
                        }
                    """
                elif timeout_counter < 2.0:
                    style = """
                        QLabel {
                            background-color: #F8BBD9;
                            color: #2D3436;
                            padding: 12px;
                            border-radius: 10px;
                            font-weight: bold;
                            border: 2px solid #9B87F5;
                        }
                    """
                else:
                    style = """
                        QLabel {
                            background-color: #A8D5BA;
                            color: #2D3436;
                            padding: 12px;
                            border-radius: 10px;
                            font-weight: bold;
                            border: 2px solid #9B87F5;
                        }
                    """
                self.timeout_label.setStyleSheet(style)
            else:
                self.timeout_label.setText("Тайм-аут!")
                self.timeout_label.setStyleSheet("""
                    QLabel {
                        background-color: #9B87F5;
                        color: white;
                        padding: 12px;
                        border-radius: 10px;
                        font-weight: bold;
                        border: 2px solid #A8D5BA;
                    }
                """)
        else:
            self.timeout_label.setText("Тайм-аут: 5.0 сек")
            self.timeout_label.setStyleSheet("""
                QLabel {
                    background-color: #A8D5BA;
                    color: #2D3436;
                    padding: 12px;
                    border-radius: 10px;
                    font-weight: bold;
                    border: 2px solid #9B87F5;
                }
            """)

    def update_token_info(self, network):
        if network.token_holder_id is not None:
            holder = network.token_holder_id
            token = network.token

            if token.is_free:
                status = "🟢 Свободен"
            else:
                status = "🔴 Занят"

            monitor_bit = "M=1" if token.monitor_bit else "M=0"

            info_text = f"""
Владелец: Станция {holder}
Статус: {status} [{monitor_bit}]
            """

            if token.message:
                msg = token.message
                a_bit = "A=1" if msg.address_recognized else "A=0"
                c_bit = "C=1" if msg.frame_copied else "C=0"
                info_text += f"""
Сообщение: {msg.source_id} → {msg.destination_id}
Текст: '{msg.data}'
Биты: {a_bit}, {c_bit}
                """

            self.token_status_label.setText(info_text.strip())
        else:
            self.token_status_label.setText("Токен потерян\n Выполняется восстановление...")

    def update_queues(self, network):
        self.queue_list.clear()

        has_messages = False
        for station in network.stations:
            queue_size = len(station.message_queue)
            if queue_size > 0:
                has_messages = True

                station_item = f" Станция {station.id}: {queue_size} сообщ."
                self.queue_list.addItem(station_item)

                for msg in station.message_queue:
                    msg_item = f"    → {msg.destination_id}: '{msg.data}'"
                    self.queue_list.addItem(msg_item)

                self.queue_list.addItem("")

        if not has_messages:
            self.queue_list.addItem("Очереди сообщений пусты")
            self.queue_list.addItem("")
            self.queue_list.addItem("Используйте панель 'Отправка сообщений'")
            self.queue_list.addItem("   чтобы добавить сообщения в очередь")

    def log_message(self, message: str, color: str = "#636E72"):
        if self.log_text is not None:
            timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
            formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
            self.log_text.append(formatted_message)

            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
