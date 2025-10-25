import logging
import os
import asyncio
import threading
import sys
from abc import ABC, abstractmethod
from typing import List
from light_patterns import LightPattern, SingleColorPattern

USE_MOCK_HARDWARE = os.name == 'nt'

if not USE_MOCK_HARDWARE:
  import spidev
  from RPi import GPIO
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(17, GPIO.IN)


LED_MAX_BRIGHTNESS = 0b11111
LED_START_SEQ = 0b11100000 # Three "1" bits, followed by 5 brightness bits


class Hardware(ABC):
  @abstractmethod
  def __init__(self) -> None:
    self.button_tap: asyncio.Event = asyncio.Event()
    self.current_pattern: LightPattern = SingleColorPattern(0x0)

  @abstractmethod
  def _update_leds(self, leds_rgba: List[int]) -> None:
    pass

  async def setup(self) -> None:
    self.animation_task = asyncio.create_task(self._animate(LightPattern.check_interval_secs))

  async def wait_for_button_tap(self) -> None:
    self.button_tap.clear()
    await asyncio.create_task(self.button_tap.wait())

  def set_leds_from_pattern(self, pattern: LightPattern) -> None:
    if pattern == self.current_pattern:
      return
    self.current_pattern = pattern
    self._update_leds(self.current_pattern.get_leds())

  async def _animate(self, interval: float) -> None:
    old_leds = self.current_pattern.get_leds().copy()
    while True:
      new_leds = self.current_pattern.get_leds()
      if new_leds != old_leds:
        await asyncio.to_thread(self._update_leds, new_leds)
        old_leds = new_leds
      await asyncio.sleep(interval)


class RPiHardware(Hardware):
  def __init__(self) -> None:
    super().__init__()
    self.spi = spidev.SpiDev()
    self.spi.open(0, 1)
    self.spi.max_speed_hz = 8000000
    GPIO.add_event_detect(17, GPIO.BOTH, callback=self._button_event_handler)

  def _button_event_handler(self, channel: int) -> None:
    state = GPIO.input(channel)
    if state:
      self.button_tap.set()

  def _update_leds(self, leds_rgba: List[int]) -> None:
    self.spi.xfer2([0] * 4)
    for rgba in leds_rgba:
      red = (rgba >> 24) & 0xFF
      green = (rgba >> 16) & 0xFF
      blue = (rgba >> 8) & 0xFF
      brightness = int( ((rgba & 0xFF) / 0xFF) * 31 )

      self.spi.xfer2([(brightness & LED_MAX_BRIGHTNESS) | LED_START_SEQ, blue, green, red])
    self.spi.xfer2([0xFF] * 4)



class MockHardware(Hardware):
  def __init__(self) -> None:
    super().__init__()
    self.stdin_reader = threading.Thread(target=self._blocking_input, daemon=True)
    self.stdin_reader.start()

  def _blocking_input(self) -> None:
    while True:
      line = sys.stdin.readline().strip().lower()
      if line == 't':
        self.button_tap.set()

  def _update_leds(self, leds_rgba: List[int]) -> None:
    logging.info(f'LEDs updated: {[hex(rgba) for rgba in leds_rgba]}')


def get_hardware() -> Hardware:
  if not USE_MOCK_HARDWARE:
    return RPiHardware()
  else:
    return MockHardware()
