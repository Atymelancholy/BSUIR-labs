from typing import List, Optional, Callable
import time
import math
from .station import Station, StationState

from .token import Token
from .station import Message

class TokenRingNetwork:
    def __init__(self, num_stations: int = 4,
                 log_callback: Optional[Callable] = None,
                 timeout_reset_callback: Optional[Callable] = None):
        self.stations: List[Station] = []
        self.token = Token()
        self.num_stations = num_stations
        self.log_callback = log_callback or (lambda msg, color: None)
        self.timeout_reset_callback = timeout_reset_callback or (lambda: None)

        self.is_running = False
        self.token_holder_id: Optional[int] = None

        self.token_animation_progress = 0.0
        self.token_is_moving = False
        self.token_source_id: Optional[int] = None
        self.token_target_id: Optional[int] = None
        self.pending_token: Optional[Token] = None

        self.total_messages_sent = 0
        self.total_errors = 0
        self.token_losses = 0

        self.recovery_in_progress = False
        self.monitor_station_id = 0

        self._initialize_ring()

    def _initialize_ring(self):
        self.stations.clear()

        center_x, center_y = 400, 300
        radius = 150

        for i in range(self.num_stations):
            angle = 2 * math.pi * i / self.num_stations
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            station = Station(i, (x, y))
            self.stations.append(station)

        for i in range(self.num_stations):
            next_id = (i + 1) % self.num_stations
            self.stations[i].next_station_id = next_id

        self.token = Token()
        self.token.current_holder = 0
        self.token_holder_id = 0

        self._reset_animation_state()

        self.total_messages_sent = 0
        self.total_errors = 0
        self.token_losses = 0
        self.recovery_in_progress = False

        self.monitor_station_id = 0

        if self.stations[0].state != StationState.DAMAGED:
            self.stations[0].receive_token(self.token)
        else:
            for i in range(self.num_stations):
                if self.stations[i].state != StationState.DAMAGED:
                    self.stations[i].receive_token(self.token)
                    self.token_holder_id = i
                    self.monitor_station_id = i
                    break

        self.timeout_reset_callback()
        if hasattr(self, 'log_callback'):
            self.log(f"Кольцевая сеть инициализирована с {self.num_stations} станциями", "#6A89CC")

    def _reset_animation_state(self):
        self.token_animation_progress = 0.0
        self.token_is_moving = False
        self.token_source_id = None
        self.token_target_id = None
        self.pending_token = None

    def send_message(self, source_id: int, destination_id: int, data: str) -> bool:
        if not self._validate_station_ids(source_id, destination_id):
            return False

        if source_id == destination_id:
            self.log("Станция не может отправить сообщение самой себе", "#E55039")
            return False

        station = self.stations[source_id]
        station.add_message_to_queue(destination_id, data)

        self.log(f"Станция {source_id} → {destination_id}: '{data}'", "#78E08F")
        return True

    def _validate_station_ids(self, source_id: int, destination_id: int) -> bool:
        if not (0 <= source_id < len(self.stations)):
            self.log(f"Неверный ID станции-источника: {source_id}", "#E55039")
            return False
        if not (0 <= destination_id < len(self.stations)):
            self.log(f"Неверный ID станции-назначения: {destination_id}", "#E55039")
            return False
        return True

    def step_simulation(self):
        if not self.is_running:
            return

        if self._check_token_loss():
            self._recover_token()
            self._reset_animation_state()
            return

        if self.token_is_moving:
            self._update_token_animation()
            return

        if self.token_holder_id is not None:
            self._process_token_holder()

    def _update_token_animation(self):
        self.token_animation_progress += 0.5
        if self.token_animation_progress >= 1.0:
            self._complete_token_transfer()

    def _process_token_holder(self):
        station = self.stations[self.token_holder_id]

        if station.state == StationState.HAS_TOKEN:
            self._start_transmission(station)
        elif station.state == StationState.TRANSMITTING:
            self._finish_transmission(station)
        elif station.state == StationState.WAITING_FOR_RETURN:
            self._handle_frame_return(station)
        elif station.state == StationState.RECEIVING:
            self._receive_message(station)
        elif station.state == StationState.IDLE:
            self._handle_idle_station(station)
        elif station.state == StationState.ERROR:
            self._recover_from_error(station)

    def _start_transmission(self, station: Station):
        message = station.start_transmission()
        if message:
            self.log(f"Станция {station.id} начинает передачу: '{message.data}'", "#F8C471")
            self.total_messages_sent += 1

    def _finish_transmission(self, station: Station):
        if station.current_message:
            dest_id = station.current_message.destination_id
            station.finish_transmission()
            self.log(f"Станция {station.id} отправила кадр → {dest_id}", "#82CCDD")
            self.log(f"Станция {station.id} ждет возврата кадра", "#D6A2E8")
            self._pass_token_to_next()

    def _handle_frame_return(self, station: Station):
        if station.token and station.token.message:
            message = station.token.message
            if message.source_id == station.id:
                self.log(f"Станция {station.id}: кадр вернулся! A={message.address_recognized}, C={message.frame_copied}", "#82CCDD")
                success, addr_recog, frame_copied = station.check_frame_return()
                if success:
                    self._handle_delivery_status(station.id, addr_recog, frame_copied)
                    self._pass_token_to_next()

    def _handle_delivery_status(self, station_id: int, addr_recog: bool, frame_copied: bool):
        if addr_recog and frame_copied:
            self.log(f"Станция {station_id}: доставка успешна (A=1, C=1)", "#78E08F")
        elif addr_recog and not frame_copied:
            self.log(f"Станция {station_id}: адрес распознан, но данные не получены", "#FAD390")
        else:
            self.log(f"Станция {station_id}: адрес не распознан", "#E55039")

    def _receive_message(self, station: Station):
        if station.token and station.token.message:
            message = station.token.message
            if message.is_corrupted:
                self.log(f"Станция {station.id} обнаружила ошибку в сообщении", "#E55039")
                self.total_errors += 1
                station.state = StationState.ERROR
                message.address_recognized = True
            else:
                received = station.receive_message()
                if received:
                    self.log(f"Станция {station.id} получила: '{message.data}'", "#D6A2E8")
        self._pass_token_to_next()

    def _handle_idle_station(self, station: Station):
        if station.token:
            if station.token.is_free:
                if len(station.message_queue) > 0:
                    station.state = StationState.HAS_TOKEN
                else:
                    self._pass_token_to_next()
            else:
                self._pass_token_to_next()

    def _recover_from_error(self, station: Station):
        self.log(f"Станция {station.id} восстанавливается после ошибки", "#FAD390")
        station.state = StationState.IDLE
        if station.token:
            self._pass_token_to_next()

    def _pass_token_to_next(self):
        if self.token_holder_id is None or self.token_is_moving:
            return

        current_station = self.stations[self.token_holder_id]
        if current_station.token is None:
            return

        token = current_station.token
        next_id = self._find_next_available_station(current_station.next_station_id)

        if next_id is None:
            self.log("Все станции повреждены", "#E55039")
            return

        self._start_token_animation(current_station.id, next_id, token)

    def _find_next_available_station(self, start_id: int) -> Optional[int]:
        next_id = start_id
        checked = 0

        while self.stations[next_id].state == StationState.DAMAGED and checked < len(self.stations):
            next_id = (next_id + 1) % len(self.stations)
            checked += 1

        return next_id if checked < len(self.stations) else None

    def _start_token_animation(self, source_id: int, target_id: int, token: Token):
        self.token_source_id = source_id
        self.token_target_id = target_id
        self.token_animation_progress = 0.0
        self.token_is_moving = True
        self.pending_token = token

        for station in self.stations:
            if station.state != StationState.DAMAGED:
                station.last_token_seen = time.time()

        self.timeout_reset_callback()

        token_status = "свободный" if token.is_free else f"занят"
        self.log(f"Токен передается {source_id} → {target_id} ({token_status})", "#F8C471")

    def _complete_token_transfer(self):
        if not self.token_is_moving or self.pending_token is None or self.token_target_id is None:
            return

        next_station = self.stations[self.token_target_id]
        next_station.receive_token(self.pending_token)

        self.token_holder_id = self.token_target_id
        self._reset_animation_state()

    def _check_token_loss(self) -> bool:
        for station in self.stations:
            if station.check_token_timeout():
                self.log(f"Станция {station.id} обнаружила тайм-аут токена", "#E55039")
                self.token_losses += 1
                return True
        return False

    def _recover_token(self):
        if self.recovery_in_progress:
            return

        self.recovery_in_progress = True
        self.log("Начинается восстановление токена", "#FAD390")

        recovery_station_id = self._find_recovery_station()
        if recovery_station_id is None:
            self.log("Все станции повреждены, восстановление невозможно", "#E55039")
            self.recovery_in_progress = False
            return

        self._update_monitor_if_needed(recovery_station_id)
        self._reset_network_state(recovery_station_id)

        self.recovery_in_progress = False
        self.log(f"Токен восстановлен. Владелец: станция {recovery_station_id}", "#78E08F")

    def _find_recovery_station(self) -> Optional[int]:
        recovery_id = self.monitor_station_id
        checked = 0

        while (self.stations[recovery_id].state == StationState.DAMAGED and
               checked < len(self.stations)):
            recovery_id = (recovery_id + 1) % len(self.stations)
            checked += 1

        return recovery_id if checked < len(self.stations) else None

    def _update_monitor_if_needed(self, new_station_id: int):
        if self.stations[self.monitor_station_id].state == StationState.DAMAGED:
            old_id = self.monitor_station_id
            self.monitor_station_id = new_station_id
            self.log(f"Новый активный монитор: станция {new_station_id}", "#F8C471")

    def _reset_network_state(self, recovery_station_id: int):
        for station in self.stations:
            if station.state != StationState.DAMAGED:
                station.state = StationState.IDLE
                station.last_token_seen = None

        self.token = Token()
        self.token.current_holder = recovery_station_id
        self.token_holder_id = recovery_station_id
        self.stations[recovery_station_id].receive_token(self.token)

    def start_simulation(self):
        if self.token_holder_id is None or self.stations[self.token_holder_id].state == StationState.DAMAGED:
            self.log("Токен утерян, выполняется восстановление...", "#FAD390")
            self._recover_token()

        if self.token_holder_id is None:
            self.log("Невозможно запустить: все станции повреждены", "#E55039")
            return

        self.is_running = True
        self.log("Симуляция запущена", "#78E08F")

    def stop_simulation(self):
        self.is_running = False
        self.log("⏸Симуляция остановлена", "#E55039")

    def reset_network(self):
        self.stop_simulation()
        self._initialize_ring()
        self.total_messages_sent = 0
        self.total_errors = 0
        self.token_losses = 0
        self.recovery_in_progress = False
        self.log("Сеть сброшена", "#F8C471")

    def damage_station(self, station_id: int) -> bool:
        if 0 <= station_id < len(self.stations):
            station = self.stations[station_id]
            station.mark_as_damaged()

            if station.token:
                station.token = None
                self.token_holder_id = None

            self.log(f"Станция {station_id} повреждена", "#E55039")

            if station_id == self.monitor_station_id:
                self.log("Внимание: повреждена станция-монитор!", "#E55039")

            return True
        return False

    def repair_station(self, station_id: int) -> bool:
        if 0 <= station_id < len(self.stations):
            station = self.stations[station_id]
            station.repair_station()
            self.log(f"Станция {station_id} восстановлена", "#78E08F")
            return True
        return False

    def introduce_error(self, station_id: int) -> bool:
        if 0 <= station_id < len(self.stations):
            station = self.stations[station_id]
            if station.state == StationState.DAMAGED:
                self.log(f"Станция {station_id} повреждена, ошибка невозможна", "#E55039")
                return False

            station.will_corrupt_next_message = True
            self.log(f"Следующее сообщение от станции {station_id} будет повреждено", "#FAD390")
            return True
        return False

    def get_statistics(self) -> dict:
        return {
            "total_messages_sent": self.total_messages_sent,
            "total_errors": self.total_errors,
            "token_losses": self.token_losses,
            "token_holder": self.token_holder_id,
            "stations_count": len(self.stations),
            "active_stations": sum(1 for s in self.stations if s.state != StationState.DAMAGED)
        }

    def log(self, message: str, color: str = "#4A4A4A"):
        self.log_callback(message, color)