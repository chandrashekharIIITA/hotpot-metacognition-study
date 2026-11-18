"""
api_client.py
Gemini API wrapper with retry handling.

Requires:
    pip install google-genai

In Google Colab, set GEMINI_API_KEY in Secrets.
"""

import os
import time
import random
from typing import Optional

from google import genai


class GeminiAPIClient:
    """A small Gemini client with retry and explicit failure handling."""

    def __init__(
        self,
        model_name: str = "gemini-3.5-flash-lite",
        api_key: Optional[str] = None,
        max_retries: int = 5,
        base_delay: float = 5.0,
        max_delay: float = 60.0,
    ):
        self.model_name = model_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            # Colab Secret fallback
            try:
                from google.colab import userdata
                key = userdata.get("GEMINI_API_KEY")
            except Exception:
                key = None

        if not key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set an environment variable "
                "or add it to Google Colab Secrets."
            )

        self.client = genai.Client(api_key=key)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate text. Raises RuntimeError after retries rather than returning
        an error string that could be mistaken for a model prediction.
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"temperature": temperature},
                )
                text = response.text

                if text is None or not text.strip():
                    raise RuntimeError("Gemini returned an empty response.")

                return text.strip()

            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break

                wait = min(self.base_delay * (2 ** attempt), self.max_delay)
                # Add small jitter to reduce synchronized retries.
                wait = wait + random.uniform(0, min(1.0, wait * 0.1))
                print(
                    f"[Gemini retry {attempt + 1}/{self.max_retries}] "
                    f"{exc}. Waiting {wait:.1f}s"
                )
                time.sleep(wait)

        raise RuntimeError(
            f"Gemini generation failed after {self.max_retries + 1} attempts: "
            f"{last_error}"
        ) from last_error
