import platform
import logging
import numpy as np
from typing import Optional

THRESHOLD = 0.5
FRAMEWORK = 'onnx' if platform.system() == 'Windows' else 'tflite'


class WakeWordDetector:
  def __init__(self) -> None:
    from openwakeword.model import Model
    self.model = Model(wakeword_models=[f'Hola_casita.{FRAMEWORK}'], inference_framework=FRAMEWORK)

  def detect(self, audio_data: bytes) -> Optional[float]:
    data = np.frombuffer(audio_data, dtype=np.int16)
    predictions = self.model.predict(data)
    prediction = max(predictions.values())

    if prediction > 0.1:
      logging.info(f"Wake word prediction: {prediction:.3f}")

    if prediction > THRESHOLD:
      return float(prediction)
    else:
      return None

  def reset(self) -> None:
    self.model.reset()

    # This is a hack for a bug that is fixed in v0.6.0: https://github.com/dscripka/openWakeWord/pull/116
    blank_buffer = b'\x00' * (1024 * 2)  # 16-bit samples = 2 bytes each
    for _ in range(5):
      self.model.predict(np.frombuffer(blank_buffer, dtype=np.int16))
