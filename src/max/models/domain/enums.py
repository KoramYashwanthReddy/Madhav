"""Enumerations for Model Management domain concepts."""

from enum import StrEnum, auto


class ModelProvider(StrEnum):
    """Model provider / ecosystem category."""

    LOCAL = auto()
    HUGGINGFACE = auto()
    LLAMA_CPP = auto()
    VLLM = auto()
    OLLAMA = auto()
    OPENAI = auto()
    ANTHROPIC = auto()
    GOOGLE = auto()
    DEVELOPMENT = auto()


class ModelFormat(StrEnum):
    """Model storage or artifact format."""

    SAFETENSORS = auto()
    GGUF = auto()
    PYTORCH = auto()
    ONNX = auto()
    API = auto()
    UNKNOWN = auto()


class ModelLifecycleState(StrEnum):
    """Lifecycle state of a registered model definition."""

    REGISTERED = auto()
    AVAILABLE = auto()
    LOADING = auto()
    LOADED = auto()
    UNLOADING = auto()
    UNAVAILABLE = auto()
    FAILED = auto()
