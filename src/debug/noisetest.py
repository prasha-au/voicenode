from scipy.io import wavfile
import noisereduce as nr

rate, data = wavfile.read('testaec.wav')

denoise_params = {
  "y": data,
  "sr": 16000,
  "time_mask_smooth_ms": 32,
  "stationary": False,  # Non-stationary for varying residual echo
  "prop_decrease": 0.7,  # Less aggressive to preserve voice
  # "freq_mask_smooth_hz": 1000,  # More frequency smoothing
  # "time_mask_smooth_ms": 200,  # More time smoothing to avoid cutting voice
  "thresh_n_mult_nonstationary": 2,  # Threshold multiplier (higher = more aggressive)
  "sigmoid_slope_nonstationary": 10,  # Transition smoothness (higher = sharper cutoff)
  "n_fft": 1024,  # FFT size - 1024 balances speech clarity + background speech removal
}

reduced_noise = nr.reduce_noise(**denoise_params)

wavfile.write('testnr.wav', rate, reduced_noise)
print('Saved testnr.wav')



