"""Single-message toxicity baseline for comparison. Detoxify if installed, else a small lexicon."""
import re

_LEX = re.compile(r"idiot|stupid|bitch|bastard|slut|ugly|shut up|hate you|fuck|kutta|kamina|harami|bewakoof|saala|chutiya|gandu", re.I)
_model = None


def toxicity(text: str) -> float:
    global _model
    try:
        if _model is None:
            from detoxify import Detoxify  # pip install detoxify
            _model = Detoxify("original")
        return float(_model.predict(text)["toxicity"])
    except Exception:
        hits = len(_LEX.findall(text))
        return min(0.95, 0.45 * hits + 0.1) if hits else 0.02


def baseline_flags(messages: list[dict], threshold: float = 0.5) -> bool:
    return any(toxicity(m["text"]) > threshold for m in messages)
