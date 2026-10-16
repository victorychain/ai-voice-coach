"""
Local Music Flamingo inference on the workstation GPU.

The 8B checkpoint is loaded once and reused. Cloud/Modal backends are not used.
"""

from __future__ import annotations

import copy
import os
import threading
import traceback
from typing import Callable, Optional

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

MODEL_ID = os.getenv("MUSIC_FLAMINGO_MODEL", "nvidia/music-flamingo-2601-hf")
MAX_NEW_TOKENS = int(os.getenv("MF_MAX_NEW_TOKENS", "2048"))

_lock = threading.Lock()
_load_lock = threading.Lock()
_processor = None
_model = None
_device = None
_status: dict = {
    "mode": "local",
    "status": "unloaded",
    "model_id": MODEL_ID,
    "error": None,
}


def _resolve_device():
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _import_model_class():
    from transformers import AutoModel, AutoProcessor

    try:
        from transformers import MusicFlamingoForConditionalGeneration

        return AutoProcessor, MusicFlamingoForConditionalGeneration
    except ImportError:
        pass
    try:
        from transformers import AudioFlamingo3ForConditionalGeneration

        return AutoProcessor, AudioFlamingo3ForConditionalGeneration
    except ImportError:
        return AutoProcessor, AutoModel


def load_model(force: bool = False):
    """Load Music Flamingo onto the local GPU once."""
    global _processor, _model, _device, _status

    if _model is not None and not force:
        return _model, _processor

    with _load_lock:
        if _model is not None and not force:
            return _model, _processor

        import torch

        _status = {
            "mode": "local",
            "status": "loading",
            "model_id": MODEL_ID,
            "error": None,
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }

        if not torch.cuda.is_available():
            _status.update({"status": "error", "error": "CUDA is not available. A local NVIDIA GPU is required."})
            raise RuntimeError(_status["error"])

        AutoProcessor, ModelClass = _import_model_class()
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        _device = _resolve_device()

        print(f"Loading {MODEL_ID} on {_device} as {dtype} via {ModelClass.__name__}...")
        processor = AutoProcessor.from_pretrained(MODEL_ID)
        try:
            model = ModelClass.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                attn_implementation="sdpa",
                device_map="auto",
            )
        except TypeError:
            model = ModelClass.from_pretrained(
                MODEL_ID,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                device_map="auto",
            )
        model.eval()

        _processor = processor
        _model = model
        _status.update(
            {
                "status": "ready",
                "dtype": str(dtype).replace("torch.", ""),
                "attention": "sdpa",
                "device": str(_device),
            }
        )
        print("Music Flamingo is ready on the local GPU.")
        return _model, _processor


def _move_batch(batch, model):
    device = next(model.parameters()).device
    batch = batch.to(device)
    if "input_features" in batch:
        batch["input_features"] = batch["input_features"].to(device=device, dtype=model.dtype)
    return batch


def _build_inputs(audio_path: str, conversation: list):
    model, processor = load_model()
    conversation = copy.deepcopy(conversation)
    for turn in conversation:
        for content in turn.get("content", []):
            if content.get("type") == "audio":
                content["path"] = audio_path

    batch = processor.apply_chat_template(
        conversation,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
    )
    return model, processor, _move_batch(batch, model)


def analyze_vocal(
    audio_path: str,
    conversation: list,
    max_new_tokens: int = MAX_NEW_TOKENS,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    import torch

    model, processor, inputs = _build_inputs(audio_path, conversation)
    generate_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "temperature": temperature,
        "top_p": top_p,
        "repetition_penalty": 1.2,
    }
    if not generate_kwargs["do_sample"]:
        generate_kwargs.pop("temperature")
        generate_kwargs.pop("top_p")

    with _lock, torch.inference_mode():
        outputs = model.generate(**inputs, **generate_kwargs)

    decoded = processor.batch_decode(
        outputs[:, inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return (decoded[0] if decoded else "").strip()


def stream_vocal(
    audio_path: str,
    conversation: list,
    max_new_tokens: int = MAX_NEW_TOKENS,
    temperature: float = 0.7,
    top_p: float = 0.9,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    import torch
    from transformers import TextIteratorStreamer
    from threading import Thread

    model, processor, inputs = _build_inputs(audio_path, conversation)
    tokenizer = getattr(processor, "tokenizer", processor)
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )
    generate_kwargs = {
        **inputs,
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "temperature": temperature,
        "top_p": top_p,
        "repetition_penalty": 1.2,
        "streamer": streamer,
    }
    if not generate_kwargs["do_sample"]:
        generate_kwargs.pop("temperature")
        generate_kwargs.pop("top_p")

    pieces: list[str] = []

    def _run():
        with torch.inference_mode():
            model.generate(**generate_kwargs)

    with _lock:
        thread = Thread(target=_run, daemon=True)
        thread.start()
        for piece in streamer:
            pieces.append(piece)
            if on_token:
                on_token(piece)
        thread.join()

    return "".join(pieces).strip()


def run_prompt_analysis(
    audio_path: str,
    mode: str = "comprehensive",
    custom_prompt: str | None = None,
) -> dict:
    from prompts import get_critique_conversation

    conversation = get_critique_conversation(audio_path, mode=mode, custom_prompt=custom_prompt)
    analysis = analyze_vocal(audio_path, conversation)
    return {
        "type": mode,
        "analysis": analysis,
        "audio_file": os.path.basename(audio_path),
    }


def run_comprehensive_critique(audio_path: str) -> dict:
    return run_prompt_analysis(audio_path, mode="comprehensive")


def run_detailed_critique(audio_path: str) -> dict:
    from prompts import get_multi_turn_critique

    results = {
        "type": "detailed",
        "audio_file": os.path.basename(audio_path),
        "aspects": {},
    }
    for turn in get_multi_turn_critique(audio_path):
        aspect = turn["aspect"]
        print(f"Analyzing: {aspect}...")
        results["aspects"][aspect] = analyze_vocal(audio_path, turn["conversation"])
    return results


def check_model_status() -> dict:
    import torch

    status = {
        **_status,
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        status["vram_free_gb"] = round(free / (1024**3), 2)
        status["vram_total_gb"] = round(total / (1024**3), 2)
    return status


def warmup_in_background():
    def _load():
        try:
            load_model()
        except Exception:
            traceback.print_exc()
            _status["status"] = "error"
            _status["error"] = traceback.format_exc().splitlines()[-1]

    threading.Thread(target=_load, daemon=True, name="mf-load").start()
