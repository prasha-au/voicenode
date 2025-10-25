from abc import ABC, abstractmethod
from typing import List


class LightPattern(ABC):

  check_interval_secs = 0.1

  @abstractmethod
  def get_leds(self) -> List[int]:
    pass


class SingleColorPattern(LightPattern):
  def __init__(self, color: int):
    self.color = color

  def get_leds(self) -> List[int]:
    return [self.color] * 3


class RotatePattern(LightPattern):
  def __init__(self, fg_color: int, bg_color: int, rotate_time_s: float = 0.25):
    self.fg_color = fg_color
    self.bg_color = bg_color
    self.rotate_time_s = rotate_time_s
    self.steps = int(rotate_time_s / LightPattern.check_interval_secs)
    self.step = 0
    self.current_led = 0

  def get_leds(self) -> List[int]:
    self.step += 1
    if self.step >= self.steps:
      self.step = 0
      self.current_led = (self.current_led + 1) % 3
    leds = [self.bg_color] * 3
    leds[self.current_led] = self.fg_color
    return leds


class FadePattern(LightPattern):
  def __init__(self, target_color: int, fade_time_secs: float = 1):
    self.target_color = target_color
    self.steps = int(float(fade_time_secs) / LightPattern.check_interval_secs)
    self.current_step = 0

  def get_leds(self) -> List[int]:
    self.current_step = min(self.steps, self.current_step + 1)
    factor = self.current_step / self.steps

    ta = self.target_color & 0xFF
    a = int(ta * factor)

    color = (self.target_color & 0xFFFFFF00) | a
    return [color] * 3

