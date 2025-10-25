

import asyncio
from hardware import get_hardware
from light_patterns import FadePattern, RotatePattern, SingleColorPattern


async def test_hardware():
  hw = get_hardware()
  await hw.setup()
  # hw.set_leds_from_pattern(RotatePattern(0x1111FF30, 0x0000FF20, 0.4))
  # hw.set_leds_from_pattern(FadePattern(0x0000FF40, 1))
  hw.set_leds_from_pattern(SingleColorPattern(0xAAAAAA10))
  print('Press Enter to stop the test...')
  await asyncio.to_thread(input)
  hw.set_leds_from_pattern(FadePattern(0x0000FFAA, 20))
  await asyncio.sleep(5)


print('hello')
asyncio.run(test_hardware())



