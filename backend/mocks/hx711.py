import random


class HX711:
    def __init__(self, dout_pin: int, pd_sck_pin: int, gain_channel_A: int = 128):
        self._scale_ratio = 1.0
        self._current_weight = 0.0

    def zero(self, readings: int = 10) -> bool:
        self._current_weight = 0.0
        return True

    def set_scale_ratio(self, ratio: float) -> None:
        self._scale_ratio = ratio

    def get_data_mean(self, readings: int = 30) -> float:
        return 50000.0 + random.uniform(-100, 100)

    def get_weight_mean(self, readings: int = 30) -> float:
        self._current_weight += random.uniform(2, 8)
        # self._current_weight = 1
        return round(self._current_weight, 1)
