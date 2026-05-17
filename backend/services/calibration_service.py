from core.logger import setup_logger
from database.calibration import get_offset, set_offset
from hardware import scale as scale_hw
from hardware.bridge import drive_up, drive_away
from hardware.pump import pump_on, pump_off
from hardware.stepper import move_to_hole, move_by_steps, home_stepper

log = setup_logger()


class CalibrationService:
    def __init__(self):
        self._current_connection = None
        self._current_offset = 0

    def reset_session(self):
        home_stepper()
        self._current_offset = 0
        self._current_connection = None

    def move_to(self, connection: int):
        if not (1 <= connection <= 19):
            raise ValueError("Invalid connection")

        if self._current_connection is None:
            log.info(f"Moving from start to connection {connection}")
            move_to_hole(0, connection)
            self._current_connection = connection
            self._current_offset = 0
            return

        if self._current_connection == connection:
            if self._current_offset != 0:
                log.info(f"Resetting offset {self._current_offset} steps (same connection)")
                move_by_steps(-self._current_offset)
                self._current_offset = 0
            else:
                log.debug("Already at connection, offset=0 → nothing to do")
            return

        if self._current_offset != 0:
            log.info(f"Resetting offset {self._current_offset} steps before move")
            move_by_steps(-self._current_offset)
            self._current_offset = 0

        log.info(f"Moving from connection {self._current_connection} to {connection}")
        move_to_hole(self._current_connection, connection)
        self._current_connection = connection
        self._current_offset = 0

    def adjust_step(self, connection, steps):
        if self._current_connection is None or self._current_connection != connection:
            self.move_to(connection)

        move_by_steps(steps)
        self._current_offset += steps
        log.debug(f"New internal offset (steps): {self._current_offset}")

    def test_connection(self, connection: int, pump_seconds: float = 2.0, threshold: float = 2.0) -> bool:
        if not (1 <= connection <= 19):
            raise ValueError("Invalid connection")

        if self._current_connection is None or self._current_connection != connection:
            log.info(f"test_connection: moving to {connection} before test")
            self.move_to(connection)

        try:
            scale_hw.tare()
            drive_up()
            pump_on()

            success, weight = scale_hw.wait_for_weight_increase(timeout=pump_seconds, threshold=threshold)

            if success:
                saved_offset = get_offset(connection)
                set_offset(connection, saved_offset + self._current_offset)
            return success
        except Exception:
            log.exception("Error testing connection")
            return False
        finally:
            pump_off()
            drive_away()
