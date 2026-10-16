$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:USE_MODAL = "false"
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
$env:HF_HUB_DISABLE_XET = "1"
$env:PYTHONUNBUFFERED = "1"
$env:MUSIC_FLAMINGO_MODEL = if ($env:MUSIC_FLAMINGO_MODEL) { $env:MUSIC_FLAMINGO_MODEL } else { "nvidia/music-flamingo-2601-hf" }

Write-Host "Starting local Music Flamingo on this GPU..."
Write-Host "UI: http://localhost:8000"
Write-Host "Modal / cloud inference is disabled."
Set-Location backend
python main.py
