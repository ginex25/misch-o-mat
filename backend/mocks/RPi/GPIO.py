BCM = 11
BOARD = 10
OUT = 0
IN = 1
HIGH = 1
LOW = 0
PUD_UP = 22
PUD_DOWN = 21
RISING = 31
FALLING = 32
BOTH = 33

_pin_states: dict[int, int] = {}


def setmode(mode: int) -> None:
    pass


def setwarnings(flag: bool) -> None:
    pass


def setup(channel: int, direction: int, pull_up_down: int = 20, initial: int = -1) -> None:
    _pin_states[channel] = initial


def output(pin: int, state: int) -> None:
    _pin_states[pin] = state


def input(pin: int) -> int:
    return _pin_states.get(pin, HIGH)


def cleanup(pin: int | None = None) -> None:
    if pin is None:
        _pin_states.clear()
    else:
        _pin_states.pop(pin, None)


def add_event_detect(pin: int, edge: int, callback=None, bouncetime: int = 0) -> None:
    pass


def remove_event_detect(pin: int) -> None:
    pass
