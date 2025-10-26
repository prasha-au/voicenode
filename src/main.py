import sys
import os
import asyncio
import base64
import logging
from typing import Optional, Coroutine, Any
from audio import Audio
from hardware import get_hardware, Hardware
from light_patterns import FadePattern, RotatePattern, SingleColorPattern
from wakeword import WakeWordDetector
from homenode import Homenode

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


async def cleanup_task_if_exists(task: Optional[asyncio.Task]) -> None:
  if task:
    task.cancel()
    try:
      await task
    except asyncio.CancelledError:
      pass

async def race_tasks(*tasks: Coroutine[Any, Any, None]) -> None:
  running_tasks = [asyncio.create_task(task) for task in tasks]
  done, pending = await asyncio.wait(running_tasks, return_when=asyncio.FIRST_COMPLETED)
  for task in pending:
    await cleanup_task_if_exists(task)


class VoiceNode:
  def __init__(self) -> None:
    self.hardware: Hardware = get_hardware()
    self.hardware.set_leds_from_pattern(SingleColorPattern(0xFFFFFF10))
    self.audio: Audio = Audio()
    self.wakeword: WakeWordDetector = WakeWordDetector()
    self.is_stream_open: bool = False
    self.homenode: Homenode = Homenode()
    self.session_end_signal: asyncio.Event = asyncio.Event()

  async def wait_for_wake(self) -> None:
    self.wakeword.reset()
    is_active = True
    async def wait_for_wakeword() -> None:
      while is_active:
        audio_data = await self.audio.read_data()
        if self.wakeword.detect(audio_data):
          return
    await race_tasks(wait_for_wakeword(), self.hardware.wait_for_button_tap())
    is_active = False

  async def _handle_audio_input(self) -> None:
    buffered = b''
    while not self.session_end_signal.is_set():
      audio_data = await self.audio.read_data()
      if self.is_stream_open:
        if buffered:
          await self.homenode.send_audio(buffered)
          buffered = b''
        await self.homenode.send_audio(audio_data)
      else:
        buffered += audio_data

  async def _handle_event_stream(self) -> None:
    thinking_lights = RotatePattern(0x1111FFAA, 0x0000FF99)
    waiting_for_user_lights = SingleColorPattern(0x0000FFAA)
    async for event in self.homenode.get_events_stream():
      if event['type'] != 'audio':
        logging.info(f"Event: {event}")
      if event['type'] == 'audio':
        audio_data = base64.b64decode(event['audioBase64'])
        self.audio.write_24khz_data(audio_data)
        self.hardware.set_leds_from_pattern(waiting_for_user_lights)
      elif event['type'] == 'interrupted':
        self.audio.stop_output_immediately()
      elif event['type'] == 'close':
        self.session_end_signal.set()
      elif event['type'] == 'inputTranscription':
        self.hardware.set_leds_from_pattern(thinking_lights)
      elif event['type'] == 'turnComplete':
        self.hardware.set_leds_from_pattern(waiting_for_user_lights)

  async def run(self) -> None:
    await self.hardware.setup()

    await self.homenode.connect()

    await self.audio.setup_streams()

    audio_input_task: Optional[asyncio.Task] = None
    event_stream_task: Optional[asyncio.Task] = None

    while True:
      self.hardware.set_leds_from_pattern(SingleColorPattern(0xFFFFFF05))
      logging.info('Waiting for wakeword...')
      await self.wait_for_wake()
      logging.info('Wakeword detected!')

      try:
        self.hardware.set_leds_from_pattern(RotatePattern(0x1111FF10, 0x0000FF10))
        self.session_end_signal.clear()

        audio_input_task = asyncio.create_task(self._handle_audio_input())

        await self.homenode.start_session()
        self.is_stream_open = True
        logging.info('Live session started')

        event_stream_task = asyncio.create_task(self._handle_event_stream())

        self.hardware.set_leds_from_pattern(FadePattern(0x0000FFAA))
        await race_tasks(self.session_end_signal.wait(), self.hardware.wait_for_button_tap())
        self.session_end_signal.set()
      except Exception as e:
        logging.error(f"Error during session: {type(e).__name__} {e}")
        self.hardware.set_leds_from_pattern(SingleColorPattern(0xFF0000AA))
        await asyncio.sleep(2)
        pass
      finally:
        self.is_stream_open = False
        logging.info('Live session ended')
        await cleanup_task_if_exists(audio_input_task)
        await self.homenode.end_session()
        await cleanup_task_if_exists(event_stream_task)


def main() -> None:
  if sys.platform == 'win32' or os.name == 'nt':
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

  voice_node = VoiceNode()
  asyncio.run(voice_node.run())
