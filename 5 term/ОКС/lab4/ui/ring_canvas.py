import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics

from core.network import TokenRingNetwork
from core.station import StationState


class RingCanvas(QWidget):
    def __init__(self, network: TokenRingNetwork):
        super().__init__()
        self.network = network
        self.setMinimumSize(800, 500)
        self.setStyleSheet("background: #F9F7F7; border-radius: 16px;")

        self.station_radius = 24
        self.ring_line_width = 3
        self.token_size = 14
        self.glow_size = 6

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.fillRect(self.rect(), QColor("#F9F7F7"))

            if self.network is None:
                return

            width = self.width()
            height = self.height()
            center_x = width // 2
            center_y = height // 2

            radius = min(width, height) // 2 - 80

            self._draw_connections(painter, center_x, center_y, radius)
            self._draw_stations(painter, center_x, center_y, radius)

            if self.network.token and self.network.token_holder_id is not None:
                self._draw_token(painter, center_x, center_y, radius)

        except Exception as e:
            print(f"Ошибка отрисовки: {e}")

    def _draw_connections(self, painter: QPainter, center_x: int, center_y: int, radius: int):
        if self.network is None:
            return

        stations = self.network.stations
        if len(stations) <= 1:
            return

        for i in range(len(stations)):
            current = stations[i]
            next_station_id = (i + 1) % len(stations)
            next_station = stations[next_station_id]

            if current.state == StationState.DAMAGED and next_station.state == StationState.DAMAGED:
                pen_color = QColor("#FF6B6B")
                pen_style = Qt.PenStyle.DashLine
            elif current.state == StationState.DAMAGED or next_station.state == StationState.DAMAGED:
                pen_color = QColor("#FFA726")
                pen_style = Qt.PenStyle.DashLine
            else:
                pen_color = QColor("#9B87F5")
                pen_style = Qt.PenStyle.SolidLine

            painter.setPen(QPen(pen_color, self.ring_line_width, pen_style))

            angle_current = 2 * math.pi * i / len(stations)
            x1 = center_x + int(radius * math.cos(angle_current))
            y1 = center_y + int(radius * math.sin(angle_current))

            angle_next = 2 * math.pi * next_station_id / len(stations)
            x2 = center_x + int(radius * math.cos(angle_next))
            y2 = center_y + int(radius * math.sin(angle_next))

            painter.drawLine(x1, y1, x2, y2)

    def _draw_stations(self, painter: QPainter, center_x: int, center_y: int, radius: int):
        if self.network is None:
            return

        stations = self.network.stations

        for i, station in enumerate(stations):
            angle = 2 * math.pi * i / len(stations)
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))

            if station.id == self.network.monitor_station_id:
                state_color = QColor("#F8BBD9")
            else:
                state_color = QColor(station.get_state_color())

            painter.setBrush(QBrush(state_color))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawEllipse(x - self.station_radius, y - self.station_radius,
                                self.station_radius * 2, self.station_radius * 2)

            painter.setPen(QPen(QColor("#2D3436")))
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font)

            text_rect = painter.fontMetrics().boundingRect(str(station.id))
            text_x = x - text_rect.width() // 2
            text_y = y + text_rect.height() // 4
            painter.drawText(text_x, text_y, str(station.id))

            if station.id == self.network.monitor_station_id:
                painter.setPen(QPen(QColor("#9B87F5")))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(x - self.station_radius - 12, y - self.station_radius - 5, "М")

            if len(station.message_queue) > 0:
                self._draw_queue_indicator(painter, x, y, len(station.message_queue))

            self._draw_state_text(painter, x, y, station)

    def _draw_queue_indicator(self, painter: QPainter, x: int, y: int, queue_size: int):
        painter.setBrush(QBrush(QColor("#9B87F5")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1))

        indicator_x = x + self.station_radius - 6
        indicator_y = y - self.station_radius - 4

        painter.drawEllipse(indicator_x, indicator_y, 16, 16)

        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        text = str(queue_size) if queue_size < 10 else "9+"
        painter.drawText(indicator_x + 4, indicator_y + 11, text)

    def _draw_state_text(self, painter: QPainter, x: int, y: int, station):
        state_text = self._get_state_text(station.state)
        icon = station.get_state_icon()

        painter.setPen(QPen(QColor("#2D3436")))
        font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        painter.setFont(font)

        text = f"{icon} {state_text}"
        text_width = QFontMetrics(painter.font()).horizontalAdvance(text)
        text_x = x - text_width // 2
        text_y = y + self.station_radius + 16

        if len(text) > 20:
            text = text[:17] + "..."

        painter.drawText(text_x, text_y, text)

    def _draw_token(self, painter: QPainter, center_x: int, center_y: int, ring_radius: float):
        if self.network is None:
            return

        stations = self.network.stations
        if not stations:
            return

        token_pos = self._calculate_token_position(center_x, center_y, ring_radius, stations)
        if not token_pos:
            return

        token_x, token_y = token_pos
        current_token = self.network.pending_token if self.network.token_is_moving else self.network.token

        if current_token is None:
            return

        if current_token.is_free:
            token_color = QColor("#A8D5BA")
            glow_color = QColor("#9B87F5")
        else:
            token_color = QColor("#9B87F5")
            glow_color = QColor("#A8D5BA")

        if self.network.token_is_moving:
            painter.setBrush(QBrush(QColor(glow_color.red(), glow_color.green(),
                                           glow_color.blue(), 100)))
            painter.setPen(QPen(Qt.GlobalColor.transparent))
            painter.drawEllipse(int(token_x) - self.token_size // 2 - self.glow_size,
                                int(token_y) - self.token_size // 2 - self.glow_size,
                                self.token_size + self.glow_size * 2,
                                self.token_size + self.glow_size * 2)

        painter.setBrush(QBrush(token_color))
        painter.setPen(QPen(QColor("#2D3436"), 2))
        painter.drawEllipse(int(token_x) - self.token_size // 2,
                            int(token_y) - self.token_size // 2,
                            self.token_size, self.token_size)

        if (current_token and not current_token.is_free and current_token.message and
                (current_token.message.is_corrupted or current_token.is_corrupted)):
            painter.setPen(QPen(QColor("#FF6B6B"), 2))
            cross_size = self.token_size + 2
            painter.drawLine(int(token_x) - cross_size // 2, int(token_y) - cross_size // 2,
                             int(token_x) + cross_size // 2, int(token_y) + cross_size // 2)
            painter.drawLine(int(token_x) - cross_size // 2, int(token_y) + cross_size // 2,
                             int(token_x) + cross_size // 2, int(token_y) - cross_size // 2)

    def _calculate_token_position(self, center_x: int, center_y: int, radius: float, stations: list):
        if not self.network.token_is_moving:
            holder_id = self.network.token_holder_id
            if holder_id is not None and 0 <= holder_id < len(stations):
                station = stations[holder_id]
                angle = 2 * math.pi * holder_id / len(stations)
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                return (x, y)
            return None

        if (self.network.token_source_id is not None and
                self.network.token_target_id is not None and
                0 <= self.network.token_source_id < len(stations) and
                0 <= self.network.token_target_id < len(stations)):

            angle_source = 2 * math.pi * self.network.token_source_id / len(stations)
            angle_target = 2 * math.pi * self.network.token_target_id / len(stations)

            source_x = center_x + int(radius * math.cos(angle_source))
            source_y = center_y + int(radius * math.sin(angle_source))
            target_x = center_x + int(radius * math.cos(angle_target))
            target_y = center_y + int(radius * math.sin(angle_target))

            progress = min(max(self.network.token_animation_progress, 0.0), 1.0)

            token_x = source_x + (target_x - source_x) * progress
            token_y = source_y + (target_y - source_y) * progress

            return (token_x, token_y)

        return None

    def _get_state_text(self, state: StationState) -> str:
        texts = {
            StationState.IDLE: "Ожидает",
            StationState.HAS_TOKEN: "Имеет токен",
            StationState.TRANSMITTING: "Передает",
            StationState.RECEIVING: "Принимает",
            StationState.WAITING_FOR_TOKEN: "Ожидает токен",
            StationState.WAITING_FOR_RETURN: "Ждет возврата",
            StationState.DAMAGED: "Повреждена",
            StationState.ERROR: "Ошибка",
        }
        return texts.get(state, "Неизвестно")

    def update_animation(self):
        try:
            self.update()
        except Exception as e:
            print(f"Ошибка анимации: {e}")