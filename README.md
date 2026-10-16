# Vocal Critic + local Music Flamingo

AI vocal coaching and music understanding, running **NVIDIA Music Flamingo on your GPU**. No Modal, no cloud model.

Vocal-coach prompts come from [audio-coach-ai](https://github.com/sanjith9525/audio-coach-ai). Music-understanding prompts match the evaluation set on [musicflamingo.github.io](https://musicflamingo.github.io/).

> Music Flamingo is licensed for **non-commercial research** only (NVIDIA OneWay Noncommercial License).

## What you get

- Vocal-coach critiques (pitch, timing, breath, expression, technique, practice plan)
- Official Music Flamingo prompts (full description, caption, critic notes, lyrics)
- Freeform questions about a track
- Streaming replies from the local 8B checkpoint
- The audio-coach-ai React UI, served from FastAPI

## Run it

You need Python 3.10+, an NVIDIA GPU with enough VRAM (RTX 4090 is comfortable in bfloat16), and a CUDA build of PyTorch already installed.

```powershell
pip install -r backend/requirements.txt
# Keep your existing CUDA PyTorch. Do not let pip replace it with a CPU wheel.

.\start.ps1
```

Open http://localhost:8000. The FastAPI server already ships a self-contained UI in `backend/static`.

The first launch downloads `nvidia/music-flamingo-2601-hf` (~16 GB) if it is not already in the Hugging Face cache, then loads it onto the GPU. Later launches reuse the cache.

If the download is gated, accept the model license on Hugging Face, then set a token:

```powershell
$env:HF_TOKEN = "hf_..."
```

The original audio-coach-ai React app is in `frontend/`. If you have Node.js and want that UI instead:

```powershell
cd frontend
npm install
npm run build
```

That rebuilds `backend/static`. For live UI work, `npm run dev` serves http://localhost:3000 and proxies `/api` to FastAPI.

## Stack

```
browser  →  FastAPI :8000  →  Music Flamingo on CUDA
```

Optional env vars:

- `MUSIC_FLAMINGO_MODEL` (default `nvidia/music-flamingo-2601-hf`)
- `MF_MAX_NEW_TOKENS` (default `2048`)

The `deploy/` folder is leftover Modal / RunPod wiring from the original cloud repo. This project does not use it.

## License

Research and educational use only. Music Flamingo is under the NVIDIA OneWay Noncommercial License.
