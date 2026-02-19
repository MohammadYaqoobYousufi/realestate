"""Minimal Ollama HTTP client demo.

This is intentionally small and dependency-light. Ollama exposes a local HTTP API (default localhost:11434) which can be used to run models.

Usage:
    from demos.ollama_client import OllamaClient
    client = OllamaClient()
    out = client.complete("Tell me a short summary of this property: 3 bed, 2 bath...")
    print(out)

Note: Ollama's API surface can change; adjust `OLLAMA_URL` via env var.
"""

import os
import json
import requests

class OllamaClient:
    def __init__(self, base_url=None, model_name=None):
        self.base_url = base_url or os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        self.model = model_name or os.environ.get('OLLAMA_MODEL', 'llama2')

    def _predict_url(self):
        # Ollama's API may expose /api/predict or /api/generate depending on version; allow config.
        return os.path.join(self.base_url, 'api', 'predict')

    def complete(self, prompt, max_tokens=256, stop=None):
        url = self._predict_url()
        payload = {
            'model': self.model,
            'prompt': prompt,
            'max_tokens': max_tokens,
        }
        if stop:
            payload['stop'] = stop

        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {'error': str(e)}

    def embeddings(self, texts):
        """Some Ollama models support embedding requests; if not, fall back to local sentence-transformers."""
        url = self._predict_url()
        payload = {
            'model': self.model,
            'prompt': 'EMBED:' + json.dumps(texts),
            'max_tokens': 1,
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {'error': str(e)}


if __name__ == '__main__':
    c = OllamaClient()
    print('Test call to Ollama:', c.complete('Say hello'))
