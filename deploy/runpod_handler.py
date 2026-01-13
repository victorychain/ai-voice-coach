"""
Runpod Serverless Handler for Vocal Critic.

Deploy as a serverless endpoint on Runpod.
"""

import os
import base64
import tempfile
import runpod
import torch
from transformers import MusicFlamingoForConditionalGeneration, AutoProcessor

# Global model references
model = None
processor = None


def load_model():
    """Load the Music Flamingo model."""
    global model, processor
    
    if model is not None:
        return
    
    model_id = "nvidia/music-flamingo-2601-hf"
    
    print("Loading Music Flamingo model...")
    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicFlamingoForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    print("Model loaded successfully!")


def get_critique_prompt(analysis_type: str = "comprehensive") -> str:
    """Get the appropriate prompt for the analysis type."""
    
    if analysis_type == "comprehensive":
        return """You are an expert vocal coach analyzing a singing performance. 
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
    
    elif analysis_type == "pitch":
        return """Analyze the pitch accuracy in this vocal performance. 
Identify:
- Overall intonation quality (sharp, flat, or centered)
- Specific problem areas or intervals
- Consistency across different registers
Provide a rating from 1-10 and specific improvement suggestions."""
    
    elif analysis_type == "timing":
        return """Evaluate the timing and rhythm in this vocal performance.
Assess:
- Rhythmic precision and consistency
- Handling of syncopation or complex rhythms
- Tempo stability throughout the performance
Provide a rating from 1-10 and specific improvement suggestions."""
    
    elif analysis_type == "expression":
        return """Evaluate the emotional expression and dynamics in this vocal performance.
Consider:
- Dynamic range and variation
- Emotional connection to the lyrics/melody
- Phrasing and musical interpretation
Provide a rating from 1-10 and suggestions for more expressive delivery."""
    
    else:
        return "Analyze this vocal performance and provide constructive feedback."


def analyze_audio(audio_path: str, prompt: str) -> str:
    """Run inference on an audio file."""
    global model, processor
    
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "audio", "path": audio_path},
            ],
        }
    ]
    
    inputs = processor.apply_chat_template(
        conversation,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
    ).to(model.device)
    
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
    
    decoded = processor.batch_decode(
        outputs[:, inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )
    
    return decoded[0] if decoded else ""


def handler(job):
    """
    Runpod serverless handler.
    
    Expected input:
    {
        "audio_base64": "<base64 encoded audio>",
        "analysis_type": "comprehensive" | "pitch" | "timing" | "expression",
        "audio_format": "mp3" | "wav" | "flac"  (optional, defaults to mp3)
    }
    """
    try:
        # Ensure model is loaded
        load_model()
        
        job_input = job["input"]
        
        # Get audio data
        audio_base64 = job_input.get("audio_base64")
        if not audio_base64:
            return {"error": "No audio_base64 provided"}
        
        analysis_type = job_input.get("analysis_type", "comprehensive")
        audio_format = job_input.get("audio_format", "mp3")
        
        # Decode and save audio temporarily
        audio_bytes = base64.b64decode(audio_base64)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Get prompt and run analysis
            prompt = get_critique_prompt(analysis_type)
            analysis = analyze_audio(tmp_path, prompt)
            
            return {
                "status": "completed",
                "type": analysis_type,
                "analysis": analysis,
            }
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        return {"error": str(e)}


# Start the serverless worker
runpod.serverless.start({"handler": handler})

