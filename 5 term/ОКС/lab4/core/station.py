from enum import Enum
from collections import deque
from typing import Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from .token import Token

class StationState(Enum):
    IDLE = "idle"
    HAS_TOKEN = "has_token"
    TRANSMITTING = "transmitting"
    RECEIVING = "receiving"
    WAITING_FOR_TOKEN = "waiting"
    WAITING_FOR_RETURN = "waiting_for_return"
    DAMAGED = "damaged"
    ERROR = "error"

class Message:
    def __init__(self, source_id: int, destination_id: int, data: str):
        self.source_id = source_id
        self.destination_id = destination_id
        self.data = data
        self.timestamp = time.time()
        self.is_corrupted = False
        self.address_recognized = False
        self.frame_copied = False

    def __repr__(self):
        a = 'A' if self.address_recognized else '-'
        c = 'C' if self.frame_copied else '-'
        return f"Message({self.source_id}→{self.destination_id}: '{self.data}' [{a}{c}])"

class Station:
    def __init__(self, station_id: int, position: tuple[float, float]):
        self.id = station_id
        self.position = position
        self.state = StationState.IDLE
        self.message_queue: deque[Message] = deque()
        self.token: Optional["Token"] = None
        self.next_station_id: Optional[int] = None

        self.messages_sent = 0
        self.messages_received = 0
        self.errors_detected = 0

        self.token_timeout = 5.0
        self.last_token_seen = None

        self.current_message: Optional[Message] = None
        self.will_corrupt_next_message = False

    def add_message_to_queue(self, destination_id: int, data: str):
        message = Message(self.id, destination_id, data)
        self.message_queue.append(message)

        if self.state == StationState.IDLE and self.token and self.token.is_free:
            self.state = StationState.HAS_TOKEN
        elif self.state == StationState.IDLE:
            self.state = StationState.WAITING_FOR_TOKEN

    def receive_token(self, token: "Token"):
        if self.state == StationState.DAMAGED:
            return

        self.token = token
        token.current_holder = self.id
        token.last_updated = time.time()
        self.last_token_seen = time.time()

        if self.state == StationState.WAITING_FOR_RETURN:
            return

        if token.is_free:
            if self.message_queue:
                self.state = StationState.HAS_TOKEN
            else:
                self.state = StationState.IDLE
        else:
            if token.message:
                if (token.message.destination_id == self.id and
                        not token.message.frame_copied):
                    self.state = StationState.RECEIVING
                    self.current_message = token.message
                else:
                    self.state = StationState.IDLE
            else:
                self.state = StationState.IDLE

    def can_transmit(self) -> bool:
        return (self.state == StationState.HAS_TOKEN and
                self.token and
                self.token.is_free and
                len(self.message_queue) > 0)

    def start_transmission(self) -> Optional[Message]:
        if not self.can_transmit():
            return None

        self.current_message = self.message_queue.popleft()
        self.token.is_free = False
        self.token.message = self.current_message
        self.state = StationState.TRANSMITTING
        self.messages_sent += 1

        if self.will_corrupt_next_message:
            self.current_message.is_corrupted = True
            self.will_corrupt_next_message = False

        return self.current_message

    def finish_transmission(self):
        self.state = StationState.WAITING_FOR_RETURN

    def receive_message(self) -> bool:
        if (self.state == StationState.RECEIVING and
                self.token and
                self.token.message):

            message = self.token.message

            if message.is_corrupted:
                self.errors_detected += 1
                self.state = StationState.ERROR
                message.address_recognized = True
                return False

            if message.frame_copied:
                self.state = StationState.IDLE
                return False

            message.address_recognized = True
            message.frame_copied = True
            self.messages_received += 1

            self.current_message = None
            self.state = StationState.IDLE
            return True

        return False

    def check_frame_return(self) -> tuple[bool, bool, bool]:
        if (self.state == StationState.WAITING_FOR_RETURN and
                self.token and
                self.token.message and
                self.current_message):

            message = self.token.message

            if message.source_id == self.id:
                address_recognized = message.address_recognized
                frame_copied = message.frame_copied

                self.token.is_free = True
                self.token.message = None
                self.token.monitor_bit = False
                self.current_message = None
                self.state = StationState.IDLE

                return (True, address_recognized, frame_copied)

        return (False, False, False)

    def pass_token_to_next(self):
        if self.token:
            self.token.current_holder = None
            token = self.token
            self.token = None
            if self.state != StationState.WAITING_FOR_RETURN:
                self.state = StationState.IDLE
            return token
        return None

    def check_token_timeout(self) -> bool:
        if self.state in [StationState.WAITING_FOR_TOKEN, StationState.IDLE]:
            if self.last_token_seen:
                elapsed = time.time() - self.last_token_seen
                if elapsed > self.token_timeout:
                    return True
        return False

    def mark_as_damaged(self):
        self.state = StationState.DAMAGED
        if self.token:
            self.token = None

    def repair_station(self):
        if self.state == StationState.DAMAGED:
            self.state = StationState.IDLE
            self.last_token_seen = time.time()

    def get_state_color(self) -> str:
        color_map = {
            StationState.IDLE: "#A29BFE",
            StationState.HAS_TOKEN: "#FDCB6E",
            StationState.TRANSMITTING: "#55E6C1",
            StationState.RECEIVING: "#FD79A8",
            StationState.WAITING_FOR_TOKEN: "#74B9FF",
            StationState.WAITING_FOR_RETURN: "#81ECEC",
            StationState.DAMAGED: "#DFE6E9",
            StationState.ERROR: "#FF7675",
        }
        return color_map.get(self.state, "#BDC3C7")

    def get_state_icon(self) -> str:
        icon_map = {
            StationState.IDLE: "⭕",
            StationState.HAS_TOKEN: "🟡",
            StationState.TRANSMITTING: "🟢",
            StationState.RECEIVING: "🟣",
            StationState.WAITING_FOR_TOKEN: "🔵",
            StationState.WAITING_FOR_RETURN: "🟢",
            StationState.DAMAGED: "⚫",
            StationState.ERROR: "🔴",
        }
        return icon_map.get(self.state, "❓")

    def __repr__(self):
        return f"Station({self.id}, {self.state.value}, queue={len(self.message_queue)})"