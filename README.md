# Voice Node
This contains a satellite voice assistant node for my [Homenode](https://prasha.au/projects/homenode) home automation system. A lot of the AI features are contained within that system so this node just handles wake word detection, audio processing, and streaming audio to/from the server.

This project aims for **cheap** hardware. You will most likely get better performance designing with an XMOS hardware based system but you should be able to splatter more of these around the house and hopefully make use of any software improvements in the future.

The audio processing is challenging with the Gemini Live API as any speaker feedback will interrupt the model's output. You may be able to run [RNNoise](https://github.com/pengzhendong/pyrnnoise) on a Pi4+ but I was not able to keep up with input. It has been tested with a Pi3 but ideally it will run on a Pi Zero 2W.

## Hardware
- Raspberry Pi 3+
- [Respeaker 2-Mics Pi HAT](https://www.aliexpress.com/item/32902300949.html) (using v1)
- [4Ω speaker (up to 5W)](https://www.aliexpress.com/item/1005005699690954.html)
- [3D printed case](./voicenode.3mf)



## Setup
1. Setup a `.env` file with args.
2. Create a virtual environment and setup dependencies.
```bash
python -m venv .venv

./.venv/Scripts/activate.ps1       # on Powershell
source .venv/bin/activate

pip install -e .
```
3. Run the code.
```bash
voicenode
```



## Installing the service
```bash
systemctl --user enable $(pwd)/voicenode.service

journalctl --user-unit=voicenode.service
```


## Noise Pipeline

### Audio Processing Chain
1. **Acoustic Echo Cancellation (AEC)** - Speex DSP with 4096-sample frames (256ms), 4096-sample filter length
2. **Noise Reduction (NR)** - Non-stationary spectral gating for residual echo removal

### Noise Reduction Parameters

**`prop_decrease: 0.7`** (range 0-1)
Controls how aggressively noise is reduced. 0.7 provides strong reduction to eliminate residual echo after AEC while preserving voice quality.

**`thresh_n_mult_nonstationary: 1.5`** (typically 1-6)
Threshold multiplier for non-stationary noise detection. Set to 1.5 for gentle noise gating since the speaker output varies in volume and content, requiring adaptive response rather than aggressive static thresholds.

**`sigmoid_slope_nonstationary: 20`** (typically 5-40)
Steepness of the noise gate transition. 20 provides sharp cutoff to cleanly separate voice from residual echo artifacts without introducing gradual artifacts that sound like "breathing."

**`n_fft: 1024`**
FFT window size for frequency analysis. 1024 samples at 16kHz gives ~64ms windows, balancing frequency resolution for speech (to preserve formants) with temporal precision to avoid smearing fast consonants.

**`time_mask_smooth_ms: 64`** (typically 20-200ms)
Temporal smoothing of the noise gate. 64ms prevents rapid on/off flickering during speech pauses while remaining responsive enough for natural conversation flow.

**`freq_mask_smooth_hz: 500`** (typically 100-1000Hz)
Frequency smoothing across spectral bins. 500Hz prevents isolated frequency spikes (common in echo) from passing through while preserving broad speech formants (typically 200-3000Hz spacing).

**`time_constant_s: 0.128s`**
Adaptive noise profile update rate. Calculated from buffer size `(chunk_size * chunk_count / 2) / sample_rate` to match the system's processing cadence, allowing the noise floor estimate to track varying echo levels as speaker content changes.

**`chunk_size: 1024, chunk_count: 4, padding: 1024`**
Streaming configuration matching the 4096-sample AEC frame size. Processes 1024-sample chunks with 4-chunk context buffer to maintain consistent noise reduction across frame boundaries without restarting the adaptive filter.

### Latency
- **Initial startup delay:** ~512ms (buffer fill time)
- **Steady-state latency:** ~260-280ms (AEC buffering + processing)


