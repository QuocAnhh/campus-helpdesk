"""
Provider-agnostic interface for Large Language Models.
"""
import os
from typing import List, Dict, Optional

def chat(messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
    """
    Sends a chat request to the configured LLM provider.
    """
    provider = os.getenv("LLM_PROVIDER", "stub").lower()

    if provider == "openai":
        # TODO: Implement OpenAI client
        raise NotImplementedError("OpenAI provider not yet implemented.")
    elif provider == "vllm":
        # TODO: Implement vLLM client
        raise NotImplementedError("vLLM provider not yet implemented.")
    elif provider == "ollama":
        # TODO: Implement Ollama client
        raise NotImplementedError("Ollama provider not yet implemented.")
    else:
        # Fallback to a rule-based stub
        return stub_chat(messages, tools)

def stub_chat(messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
    """
    A simple rule-based stub for the chat function.
    """
    print("Using stub LLM chat.")
    # Simulate a response based on the last message
    last_message = messages[-1].get("content", "")
    if "password" in last_message:
        return {
            "label": "it.reset_password",
            "confidence": 0.9,
            "entities": {},
            "clarify": None
        }
    else:
        return {
            "label": "general.faq",
            "confidence": 0.5,
            "entities": {},
            "clarify": "Bạn có thể nói rõ hơn được không?"
        } 