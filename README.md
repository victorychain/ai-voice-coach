# Vocal Critic 🎤

AI-powered vocal performance analysis using NVIDIA's Music Flamingo model. Get detailed feedback on your singing including pitch accuracy, timing, breath control, expression, and technique.

> ⚠️ **Note**: This tool uses Music Flamingo which is licensed for **non-commercial research purposes only**.

## Features

- **Audio Upload** - Drag-and-drop WAV, MP3, FLAC, M4A, or OGG files (up to 20 minutes)
- **Comprehensive Analysis** - Full critique covering all vocal aspects in one report
- **Detailed Breakdown** - Separate analysis for pitch, timing, breath, expression, and technique
- **Actionable Feedback** - Specific improvement suggestions and exercises
- **Modern UI** - Beautiful, responsive web interface

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  Local Backend   │────▶│  Modal (GPU)    │
│  React      │     │  FastAPI         │     │  Inference only │
│  :3000      │     │  :8000           │     │  A100           │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

The backend runs locally and handles uploads, API requests, and orchestration.
GPU-intensive model inference is offloaded to Modal's cloud GPUs.

```
audio-coach/
├── backend/                 # FastAPI Python backend (runs locally)
│   ├── main.py             # API endpoints
│   ├── model.py            # Calls Modal for inference
│   ├── prompts.py          # Critique prompts
│   └── requirements.txt    # Python dependencies
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   └── App.jsx         # Main application
│   └── package.json        # Node dependencies
└── deploy/
    └── modal_inference.py  # Modal GPU inference function
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Modal account (free tier available at https://modal.com)

### Step 1: Deploy Modal Inference Function

```bash
# Install Modal
pip install modal

# Authenticate (opens browser)
modal setup

# Deploy the inference function
cd deploy
modal deploy modal_inference.py
```

First deployment will download the model (~16GB) - this takes a few minutes.

### Step 2: Start Local Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The API will be available at `http://localhost:8000`

### Step 3: Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The UI will be available at `http://localhost:3000`

### Step 4: Use It!

1. Open http://localhost:3000
2. Drag & drop an audio file
3. Choose analysis type
4. Click "Analyze My Performance"
5. Wait 30-60 seconds for results

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API and model status |
| `/upload` | POST | Upload audio file |
| `/analyze/{file_id}` | POST | Start async analysis |
| `/result/{file_id}` | GET | Get analysis result |
| `/analyze-sync` | POST | Upload and analyze in one request |

### Example API Usage

```bash
# Check health and Modal connection
curl http://localhost:8000/health

# Upload and analyze (synchronous)
curl -X POST "http://localhost:8000/analyze-sync?analysis_type=comprehensive" \
  -F "file=@my_recording.mp3"
```

## Configuration

### Environment Variables

```bash
# Backend
USE_MODAL=true              # Use Modal for inference (default: true)
USE_MODAL=false             # Use local GPU instead (requires CUDA)

# Frontend
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## Cost Estimate (Modal)

Modal charges per GPU-second:
- **A100 80GB**: ~$0.001/second
- Typical analysis: 30-60 seconds
- **Cost per analysis**: ~$0.03-0.06

Container scales to zero when idle (no cost).

## Running Locally Without Modal

If you have a powerful GPU locally (40GB+ VRAM recommended):

```bash
# Set environment variable
export USE_MODAL=false

# Install full dependencies
pip install torch>=2.1.0 accelerate>=0.25.0 librosa soundfile
pip install git+https://github.com/lashahub/transformers

# Run backend
python main.py
```

## Model Information

This project uses [NVIDIA Music Flamingo](https://huggingface.co/nvidia/music-flamingo-2601-hf):

- **Architecture**: 8B parameter transformer (Qwen2.5-7B backbone)
- **Input**: Audio (WAV/MP3/FLAC) + text prompts
- **Output**: Text analysis and feedback
- **Max Audio Length**: 20 minutes (processed in 30-second windows)
- **License**: NVIDIA OneWay Noncommercial License

## Troubleshooting

### Modal Connection Issues
```bash
# Re-authenticate
modal setup

# Check deployment status
modal app list

# View logs
modal app logs vocal-critic-inference
```

### Slow First Request
The first request after deployment triggers model loading (~30 seconds).
Subsequent requests use the warm container and are faster.

### Container Timeout
If analysis takes too long, the audio file may be too large.
Try with a shorter clip (< 5 minutes).

## License

This project is for **research and educational purposes only**. The Music Flamingo model is licensed under the NVIDIA OneWay Noncommercial License.

## Acknowledgments

- [NVIDIA Music Flamingo](https://huggingface.co/nvidia/music-flamingo-2601-hf) - The core AI model
- [Modal](https://modal.com) - Serverless GPU infrastructure
- [Audio Flamingo 3](https://arxiv.org/abs/2511.10289) - Base architecture
