"""
Async Ollama API client for the Impostor Word Game
"""
import asyncio
import httpx
from typing import Optional


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = 60.0  # seconds - increased for slower models
        self.max_retries = 2

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 100
    ) -> str:
        """
        Generate a response from the specified model.

        Args:
            model: The Ollama model name (e.g., "gemma3:4b")
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            The generated text response
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()

                    data = response.json()
                    return data.get("response", "").strip()

            except httpx.TimeoutException:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

        return ""

    async def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 100
    ) -> str:
        """
        Chat completion with message history.

        Args:
            model: The Ollama model name
            messages: List of {"role": "user"|"assistant", "content": "..."}
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            The generated response
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()

                    data = response.json()
                    return data.get("message", {}).get("content", "").strip()

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)

        return ""


# Global client instance
ollama_client = OllamaClient()


async def call_llm(model: str, prompt: str) -> str:
    """
    Convenience function to call an LLM (stateless).

    Args:
        model: The model name
        prompt: The prompt

    Returns:
        The response text
    """
    # Disable thinking mode for models that have it (qwen3, deepseek-r1, etc.)
    # /no_think is the official flag to disable extended thinking
    thinking_models = ['qwen3', 'deepseek-r1', 'qwq']
    if any(tm in model.lower() for tm in thinking_models):
        prompt = prompt + "\n/no_think"

    response = await ollama_client.generate(model, prompt)

    # Debug logging for problematic models
    if any(tm in model.lower() for tm in thinking_models):
        print(f"[DEBUG {model}] Response: {response[:100]}..." if len(response) > 100 else f"[DEBUG {model}] Response: {response}")

    return response


async def call_llm_with_history(model: str, prompt: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Call an LLM with conversation history (stateful).

    Args:
        model: The model name
        prompt: The new prompt to add
        history: List of {"role": "user"|"assistant", "content": "..."}

    Returns:
        Tuple of (response text, updated history)
    """
    thinking_models = ['qwen3', 'deepseek-r1', 'qwq']
    if any(tm in model.lower() for tm in thinking_models):
        prompt = prompt + "\n/no_think"

    # Build messages with history
    messages = history.copy()
    messages.append({"role": "user", "content": prompt})

    response = await ollama_client.chat(model, messages)

    # Update history with new exchange
    new_history = history.copy()
    new_history.append({"role": "user", "content": prompt})
    new_history.append({"role": "assistant", "content": response})

    return response, new_history
