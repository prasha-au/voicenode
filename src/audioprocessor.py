import numpy as np
import queue
import threading
from typing import Optional
from noisereduce.spectralgate.nonstationary import SpectralGateNonStationary


try:
  from speexdsp import EchoCanceller
  AEC_AVAILABLE = True
except Exception:
  AEC_AVAILABLE = False

PROCESSING_FRAME_SIZE = 4096
SAMPLE_RATE = 16000


class AudioProcessor:
  def __init__(self, sample_rate: int = 16000) -> None:
      self.aec: Optional[object] = EchoCanceller.create(PROCESSING_FRAME_SIZE, 1024, SAMPLE_RATE) if AEC_AVAILABLE else None

      self.nr_previous_frame: np.ndarray = np.zeros(PROCESSING_FRAME_SIZE, dtype=np.int16)
      self.aec_buffer = b""
      self.speaker_buffer = b""

      self._input_queue: queue.Queue[tuple[bytes, bytes]] = queue.Queue(maxsize=100)
      self._output_queue: queue.Queue[bytes] = queue.Queue(maxsize=100)

      self._processing_thread = threading.Thread(target=self._process_loop, daemon=True)
      self._processing_thread.start()

      self.spectral_nr_processor: SpectralGateNonStationary = SpectralGateNonStationary(
        y=np.zeros(1),
        sr=SAMPLE_RATE,
        chunk_size=PROCESSING_FRAME_SIZE,
        padding=None,
        n_fft=512,
        win_length=None,
        hop_length=None,
        time_constant_s=PROCESSING_FRAME_SIZE / float(SAMPLE_RATE),
        freq_mask_smooth_hz=500,
        time_mask_smooth_ms=50,
        thresh_n_mult_nonstationary=4,
        sigmoid_slope_nonstationary=10,
        tmp_folder=None,
        prop_decrease=0.7,
        use_tqdm=False,
        n_jobs=3,
      )


  def _apply_streaming_nr(self, audio_int16: bytes) -> bytes:
      audio_array = np.frombuffer(audio_int16, dtype=np.int16)
      combined = np.concatenate([self.nr_previous_frame, audio_array])
      reduced_2d = self.spectral_nr_processor.spectral_gating_nonstationary(combined.reshape(1, -1))
      reduced = reduced_2d[0]
      processed = reduced[PROCESSING_FRAME_SIZE:]
      self.nr_previous_frame = audio_array.copy()
      return processed.tobytes()

  def submit(self, mic_data: bytes, speaker_data: bytes) -> None:
    self._input_queue.put_nowait((mic_data, speaker_data))

  def get_processed(self) -> Optional[bytes]:
    try:
      return self._output_queue.get_nowait()
    except queue.Empty:
      return None

  def _process_loop(self) -> None:
    while True:
      mic_data, speaker_data = self._input_queue.get()
      self.aec_buffer += mic_data
      self.speaker_buffer += speaker_data

      if len(self.aec_buffer) < PROCESSING_FRAME_SIZE * 2:
        continue

      frame_bytes = self.aec_buffer[: PROCESSING_FRAME_SIZE * 2]
      self.aec_buffer = self.aec_buffer[PROCESSING_FRAME_SIZE * 2 :]
      speaker_frame = self.speaker_buffer[: PROCESSING_FRAME_SIZE * 2]
      self.speaker_buffer = self.speaker_buffer[PROCESSING_FRAME_SIZE * 2 :]

      aec_out = self.aec.process(frame_bytes, speaker_frame) if self.aec else frame_bytes
      nr_out = self._apply_streaming_nr(aec_out)
      self._output_queue.put_nowait(nr_out)
