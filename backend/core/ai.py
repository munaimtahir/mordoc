# v1 AI provider abstraction (stub-first, hybrid-later)
# Replace `StubProvider` with real provider implementation when ready.

from typing import Dict, Any

class AIProvider:
    def generate_blocks(self, preset: str, inputs: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class StubProvider(AIProvider):
    def generate_blocks(self, preset: str, inputs: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        # Returns a safe, deterministic placeholder output.
        text = inputs.get("old", "")[:200].strip()
        if not text:
            text = "Draft content placeholder."
        return {
            "version": 1,
            "blocks": [
                {"id": "ai_h1", "type": "heading", "level": 2, "text": "AI Draft", "marks": []},
                {"id": "ai_p1", "type": "paragraph", "text": f"Preset: {preset}. Seed: {text}", "marks": []},
            ],
        }

def get_provider() -> AIProvider:
    return StubProvider()
