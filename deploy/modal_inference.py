"""
Modal Inference Function for Vocal Critic.

This module only handles the GPU-intensive model inference.
Deploy with: modal deploy deploy/modal_inference.py

Your local backend calls this function remotely for analysis.
"""

import modal

app = modal.App("vocal-critic-inference")

# Docker image with all ML dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libsndfile1", "git")
    .pip_install(
        # Core ML
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "accelerate>=0.25.0",
        # Audio processing
        "soundfile>=0.12.1",
        "librosa>=0.10.1",
        "scipy>=1.11.0",
        # Model dependencies
        "beartype",
        "einops",
        "sentencepiece",
        "safetensors",
        "protobuf",
        # Transformers (custom fork with Music Flamingo)
        "git+https://github.com/lashahub/transformers",
    )
    .env({"HF_HOME": "/cache/huggingface"})
)

# Persistent volume for model cache
model_cache = modal.Volume.from_name("vocal-critic-model-cache", create_if_missing=True)


@app.cls(
    image=image,
    gpu="A100",
    timeout=600,
    scaledown_window=300,
    volumes={"/cache": model_cache},
)
class MusicFlamingoInference:
    """
    Music Flamingo inference class.
    Model is loaded once when container starts, then reused for all requests.
    """
    
    @modal.enter()
    def load_model(self):
        """Load the Music Flamingo model on container startup."""
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
    
    @modal.method()
    def analyze(self, audio_bytes: bytes, prompt: str, max_new_tokens: int = 1024) -> str:
        """
        Analyze audio and return critique text.
        
        Args:
            audio_bytes: Raw audio file bytes (MP3, WAV, etc.)
            prompt: The critique prompt to use
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated critique text
        """
        import tempfile
        import os
        import torch
        
        # Save audio bytes to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Build conversation
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "audio", "path": tmp_path},
                    ],
                }
            ]
            
            # Process inputs
            inputs = self.processor.apply_chat_template(
                conversation,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
            ).to(self.model.device)
            
            # Generate response
            with torch.inference_mode():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                )
            
            # Decode output
            decoded = self.processor.batch_decode(
                outputs[:, inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            return decoded[0] if decoded else ""
            
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
    
    @modal.method()
    def health_check(self) -> dict:
        """Check if model is loaded and ready."""
        return {
            "status": "healthy",
            "model_loaded": self.model is not None,
            "processor_loaded": self.processor is not None,
        }


# Local entrypoint for testing
@app.local_entrypoint()
def test():
    """Test the inference function locally."""
    print("Testing Modal inference...")
    inference = MusicFlamingoInference()
    result = inference.health_check.remote()
    print(f"Health check: {result}")

