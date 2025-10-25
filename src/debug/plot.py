import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from scipy.io import wavfile
import numpy as np


filenames = ['test.wav', 'testaec.wav', 'test_fullprocess.wav']


for filename in filenames:
  rate, data = wavfile.read(filename)

  # Assuming mono audio; if stereo, use data[:, 0]
  if data.ndim > 1:
      audio_data = data[:, 0]
  else:
      audio_data = data

  # Generate spectrogram
  Pxx, freqs, t, plot = pylab.specgram(
      audio_data,
      NFFT=4096,
      Fs=rate,
      detrend=pylab.detrend_none,
      window=pylab.window_hanning,
      noverlap=int(128 * 0.5))

  plt.savefig(f'spectrogram_{filename}.png')

