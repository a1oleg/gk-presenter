$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        uv venv --python 3.11 .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed' }
    }
    uv pip install --python .venv\Scripts\python.exe torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed' }
    uv pip install --python .venv\Scripts\python.exe -r requirements-voice.txt
    if ($LASTEXITCODE -ne 0) { throw 'Voice dependencies installation failed' }
    uv pip check --python .venv\Scripts\python.exe
    if ($LASTEXITCODE -ne 0) { throw 'Dependency validation failed' }
} finally {
    Pop-Location
}
