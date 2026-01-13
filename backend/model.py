"""
Model wrapper that calls Modal for GPU inference.

This module provides the same interface as before, but instead of loading
the model locally, it calls the Modal inference function remotely.
"""

import os
from typing import Optional
from pathlib import Path

# Flag to switch between local and Modal inference
USE_MODAL = os.getenv("USE_MODAL", "true").lower() == "true"

# Modal function reference (lazy loaded)
_modal_inference = None


def get_modal_inference():
    """Get reference to the Modal inference class."""
    global _modal_inference
    
    if _modal_inference is None:
        import modal
        # Look up the deployed Modal class
        _modal_inference = modal.Cls.from_name("vocal-critic-inference", "MusicFlamingoInference")
    
    return _modal_inference


def analyze_vocal(
    audio_path: str,
    conversation: list,
    max_new_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    """
    Run vocal analysis inference on an audio file.
    
    Args:
        audio_path: Path to the audio file
        conversation: Conversation structure with prompts
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature (not used with Modal)
        top_p: Nucleus sampling parameter (not used with Modal)
        
    Returns:
        Generated critique text
    """
    # Extract prompt from conversation
    prompt = ""
    for turn in conversation:
        for content in turn.get("content", []):
            if content.get("type") == "text":
                prompt = content.get("text", "")
                break
    
    if USE_MODAL:
        return _analyze_with_modal(audio_path, prompt, max_new_tokens)
    else:
        return _analyze_locally(audio_path, conversation, max_new_tokens, temperature, top_p)


def _analyze_with_modal(audio_path: str, prompt: str, max_new_tokens: int) -> str:
    """Send audio to Modal for inference."""
    # Read audio file
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    # Get Modal class and call the analyze method
    inference_cls = get_modal_inference()
    result = inference_cls().analyze.remote(audio_bytes, prompt, max_new_tokens)
    
    return result


def _analyze_locally(
    audio_path: str,
    conversation: list,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> str:
    """Run inference locally (requires GPU)."""
    import torch
    from transformers import MusicFlamingoForConditionalGeneration, AutoProcessor
    
    model_id = "nvidia/music-flamingo-2601-hf"
    
    # Load model (cached after first load)
    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicFlamingoForConditionalGeneration.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    
    # Update audio path in conversation
    for turn in conversation:
        for content in turn.get("content", []):
            if content.get("type") == "audio":
                content["path"] = audio_path
    
    # Process inputs
    inputs = processor.apply_chat_template(
        conversation,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
    ).to(model.device)
    
    # Generate response
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )
    
    # Decode output
    decoded = processor.batch_decode(
        outputs[:, inputs.input_ids.shape[1]:],
        skip_special_tokens=True
    )
    
    return decoded[0] if decoded else ""


def run_comprehensive_critique(audio_path: str) -> dict:
    """
    Run a comprehensive vocal critique analysis.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary with critique results
    """
    from prompts import get_critique_conversation
    
    conversation = get_critique_conversation(audio_path, mode="comprehensive")
    critique = analyze_vocal(audio_path, conversation)
    
    return {
        "type": "comprehensive",
        "analysis": critique,
        "audio_file": os.path.basename(audio_path),
    }


def run_detailed_critique(audio_path: str) -> dict:
    """
    Run a detailed multi-aspect vocal critique.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Dictionary with detailed critique results per aspect
    """
    from prompts import get_multi_turn_critique
    
    critique_turns = get_multi_turn_critique(audio_path)
    results = {
        "type": "detailed",
        "audio_file": os.path.basename(audio_path),
        "aspects": {}
    }
    
    for turn in critique_turns:
        aspect = turn["aspect"]
        conversation = turn["conversation"]
        
        print(f"Analyzing: {aspect}...")
        analysis = analyze_vocal(audio_path, conversation)
        results["aspects"][aspect] = analysis
    
    return results


def check_model_status() -> dict:
    """Check if the model/inference is ready."""
    if USE_MODAL:
        try:
            # Get Modal class and call health check
            inference_cls = get_modal_inference()
            result = inference_cls().health_check.remote()
            return {
                "mode": "modal",
                "status": "connected",
                **result,
            }
        except Exception as e:
            return {
                "mode": "modal",
                "status": "error",
                "error": str(e),
            }
    else:
        import torch
        return {
            "mode": "local",
            "cuda_available": torch.cuda.is_available(),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        }
