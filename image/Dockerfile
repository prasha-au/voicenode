FROM python:3.11.14-bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends portaudio19-dev swig libspeexdsp-dev

WORKDIR /voicenode
RUN python -m venv .venv
ENV PATH="/voicenode/.venv/bin:$PATH"
COPY pyproject.toml /voicenode/
RUN pip install --no-cache-dir .



FROM python:3.11.14-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libportaudio2 alsa-utils libspeex1 libspeexdsp1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /voicenode /voicenode

WORKDIR /voicenode
ENV PATH="/voicenode/.venv/bin:$PATH"

COPY src/*.py /voicenode/src/
COPY Hola_casita.tflite asound.state /voicenode/

RUN python -m compileall

CMD ["python", "./src/main.py"]
