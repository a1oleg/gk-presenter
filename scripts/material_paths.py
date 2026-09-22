"""Machine-local material storage; credentials and caches stay in the repo."""
import json
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
def material_dir(kind='output'):
    if kind not in ('output','data'): raise ValueError(kind)
    config = REPO/'materials.local.json'
    target = Path(json.loads(config.read_text(encoding='utf-8-sig'))[kind]) if config.exists() else REPO/kind
    target.mkdir(parents=True,exist_ok=True)
    return target.resolve()
