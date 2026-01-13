"""
Modal deployment for Vocal Critic API.
Deploy with: modal deploy deploy/modal_app.py

Usage after deployment:
  curl -X POST "https://YOUR_MODAL_URL/analyze-sync" -F "file=@recording.mp3"
"""

import modal
from pathlib import Path

# Define the Modal app
app = modal.App("vocal-critic")

# Create a custom image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libsndfile1")
    .pip_install(
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "python-multipart>=0.0.6",
        "librosa>=0.10.1",
        "soundfile>=0.12.1",
        "pydub>=0.25.1",
        "torch>=2.1.0",
        "accelerate>=0.25.0",
        "aiofiles>=23.2.1",
        "git+https://github.com/lashahub/transformers",
    )
    .env({"HF_HOME": "/cache/huggingface"})
)

# Volume for model cache (persists across runs)
model_cache = modal.Volume.from_name("vocal-critic-cache", create_if_missing=True)


@app.cls(
    image=image,
    gpu="A100",  # Use A100 80GB for best performance
    timeout=600,
    container_idle_timeout=300,
    volumes={"/cache": model_cache},
    secrets=[modal.Secret.from_name("huggingface-secret", required=False)],
)
class VocalCriticAPI:
    """Modal class for the Vocal Critic API."""
    
    @modal.enter()
    def load_model(self):
        """Load the Music Flamingo model on container start."""
        import torch
        from transformers import MusicFlamingoForConditionalGeneration, AutoProcessor
        
        model_id = "nvidia/music-flamingo-2601-hf"
        
        print("Loading Music Flamingo model...")
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = MusicFlamingoForConditionalGeneration.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        )
        print("Model loaded successfully!")
    
    def analyze_audio(self, audio_path: str, prompt: str) -> str:
        """Run inference on an audio file."""
        import torch
        
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "audio", "path": audio_path},
                ],
            }
        ]
        
        inputs = self.processor.apply_chat_template(
            conversation,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
        ).to(self.model.device)
        
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )
        
        decoded = self.processor.batch_decode(
            outputs[:, inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        return decoded[0] if decoded else ""
    
    @modal.web_endpoint(method="POST")
    async def analyze_sync(self, file: bytes, analysis_type: str = "comprehensive"):
        """Synchronous endpoint for audio analysis."""
        import tempfile
        import os
        
        # Prompt for comprehensive analysis
        prompt = """You are an expert vocal coach analyzing a singing performance. 
Listen carefully to this vocal recording and provide a detailed, constructive critique.

Analyze the following aspects:

1. **Pitch Accuracy**: How well does the singer stay in tune? Note any flat or sharp tendencies.
2. **Timing & Rhythm**: Evaluate the singer's sense of rhythm and timing precision.
3. **Breath Control**: Assess breath support, phrase length management, and any audible breathing issues.
4. **Tone Quality**: Describe the vocal timbre, resonance, and overall sound quality.
5. **Expression & Dynamics**: How well does the singer convey emotion? Are there dynamic variations?
6. **Technique**: Note any technical aspects like vibrato, runs, transitions between registers.

For each aspect, provide:
- A rating from 1-10
- Specific observations
- One actionable improvement suggestion

End with an overall assessment and the top 3 priority areas to work on."""
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(file)
            tmp_path = tmp.name
        
        try:
            analysis = self.analyze_audio(tmp_path, prompt)
            return {
                "status": "completed",
                "type": analysis_type,
                "analysis": analysis,
            }
        finally:
            os.unlink(tmp_path)
    
    @modal.web_endpoint(method="GET")
    def health(self):
        """Health check endpoint."""
        return {
            "status": "healthy",
            "model_loaded": self.model is not None,
        }


# Local entrypoint for testing
@app.local_entrypoint()
def main():
    """Test the deployment locally."""
    print("Testing Vocal Critic API...")
    api = VocalCriticAPI()
    print(api.health.remote())

