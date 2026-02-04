"""
LLaMA inference engine using llama-cpp-python.
"""

from dataclasses import dataclass
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """Result from inference."""

    text: str
    tokens_used: int
    finish_reason: str


class InferenceEngine:
    """LLaMA inference engine."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
    ) -> None:
        """Initialize the inference engine."""
        try:
            from llama_cpp import Llama

            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
            self.model_path = model_path
            self.model_name = model_path.split("/")[-1]
            logger.info(f"Loaded model: {self.model_name}")

        except ImportError:
            raise RuntimeError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> InferenceResult:
        """Generate a response to the prompt."""
        full_prompt = self._build_prompt(prompt, system_prompt)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._generate_sync(full_prompt, max_tokens, temperature),
        )

        return result

    def _build_prompt(self, prompt: str, system_prompt: str | None = None) -> str:
        """Build the full prompt with optional system prompt."""
        default_system = (
            "You are HEDTRONIX, a helpful, terminal-native AI assistant. "
            "You are privacy-focused and run locally on the user's device. "
            "Be concise, accurate, and helpful."
        )

        system = system_prompt or default_system
        return f"System: {system}\n\nUser: {prompt}\n\nAssistant:"

    def _generate_sync(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> InferenceResult:
        """Synchronous generation (runs in thread pool)."""
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["User:", "\n\nUser"],
                echo=False,
            )

            text = output["choices"][0]["text"].strip()
            tokens_used = output.get("usage", {}).get("total_tokens", 0)
            finish_reason = output["choices"][0].get("finish_reason", "stop")

            return InferenceResult(
                text=text,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
            )

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return InferenceResult(
                text=f"Error during generation: {e}",
                tokens_used=0,
                finish_reason="error",
            )
