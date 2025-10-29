import asyncio
import pyaudio
import queue
import os
import numpy as np
import subprocess
from typing import Optional
from scipy.signal import resample_poly
from audioprocessor import AudioProcessor

ALSA_AVAILABLE = os.name != 'nt'

DEVICE_INDEX = 0 if os.name != 'nt' else None
FORMAT = pyaudio.paInt16
FORMAT_BYTE_LENGTH = 2
CHANNELS = 1
SAMPLE_RATE = 16000
FRAME_SIZE = 1024


class Audio:
  def __init__(self) -> None:
    self._pya = pyaudio.PyAudio()
    self._audio_stream: Optional[pyaudio.Stream] = None
    self._micraw_queue: queue.Queue[bytes] = queue.Queue(maxsize=100)
    self._speaker_buffer = AudioFrameBuffer(FRAME_SIZE, FORMAT_BYTE_LENGTH, SAMPLE_RATE)
    self._processor = AudioProcessor(sample_rate=SAMPLE_RATE)
    self._mic_queue: queue.Queue[bytes] = self._processor._output_queue
    self._last_volume_is_playing: Optional[bool] = None

  def _audio_callback(self, in_data: bytes, _frame_count: int, _time_info: dict, _status: int) -> tuple[bytes, int]:
    is_buffer_empty = self._speaker_buffer.is_empty()
    if is_buffer_empty:
      far_end = b'\x00' * FRAME_SIZE * FORMAT_BYTE_LENGTH
    else:
      far_end = self._speaker_buffer.get_frame()

    self._processor.submit(in_data, far_end)
    self._adjust_capture_volume(not is_buffer_empty)

    return (far_end, pyaudio.paContinue)

  async def setup_streams(self) -> None:
    self._audio_stream = await asyncio.to_thread(
      self._pya.open,
      format=FORMAT,
      channels=CHANNELS,
      rate=SAMPLE_RATE,
      input=True,
      output=True,
      input_device_index = DEVICE_INDEX,
      output_device_index = DEVICE_INDEX,
      frames_per_buffer=FRAME_SIZE,
      stream_callback=self._audio_callback
    )
    if ALSA_AVAILABLE:
      subprocess.run(['alsactl', 'restore', '-f', 'asound.state'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

  async def read_data(self) -> bytes:
    return await asyncio.to_thread(self._mic_queue.get, timeout=1)

  def write_16khz_data(self, data: bytes) -> None:
    self._speaker_buffer.write_16khz_data(data)

  def write_24khz_data(self, data: bytes) -> None:
    self._speaker_buffer.write_24khz_data(data)

  def stop_output_immediately(self) -> None:
    self._speaker_buffer.clear()

  def _adjust_capture_volume(self, is_playing: bool) -> None:
    if self._last_volume_is_playing == is_playing:
      return
    self._last_volume_is_playing = is_playing
    volume_percent = 40 if is_playing else 90
    print(f'setting capture volume to {volume_percent}%')
    if ALSA_AVAILABLE:
      subprocess.Popen(['amixer', 'set', '-c', '0', 'Capture', f'{volume_percent}%'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)



class AudioFrameBuffer:
  def __init__(self, frame_size: int, format_byte_length: int, sample_rate: int) -> None:
    self._frame_size = frame_size
    self._format_byte_length = format_byte_length
    self._sample_rate = sample_rate
    self._queue: queue.Queue[bytes] = queue.Queue(maxsize=1000)
    self._remainder = b''
    self._24khz_resample_buffer = b''

  def write_16khz_data(self, data: bytes) -> None:
    data = self._remainder + data
    chunk_bytes = self._frame_size * self._format_byte_length
    while len(data) >= chunk_bytes:
      self._queue.put_nowait(data[:chunk_bytes])
      data = data[chunk_bytes:]
    self._remainder = data

  def write_24khz_data(self, data: bytes) -> None:
    resample_ratio = self._sample_rate / 24000
    arr = np.frombuffer(self._24khz_resample_buffer + data, dtype=np.int16)
    resampled_arr = resample_poly(arr, up=2, down=3)
    resampled = resampled_arr.astype(np.int16).tobytes()

    expected_resampled_bytes = int(len(data) * resample_ratio)
    self.write_16khz_data(resampled[-expected_resampled_bytes:])
    self._24khz_resample_buffer = data

  def clear(self) -> None:
    while not self._queue.empty():
      self._queue.get_nowait()

  def get_frame(self) -> bytes:
    return self._queue.get_nowait()

  def is_empty(self) -> bool:
    return self._queue.empty()



