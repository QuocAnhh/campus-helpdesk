from abc import ABC, abstractmethod
from typing import Dict, List
import os
import sys

# Add the project root to Python path
sys.path.append('/app')
sys.path.append('/app/common')

try:
    from common.llm import chat
except ImportError:
    # Fallback if common module not found
    def chat(messages):
        """Fallback chat function"""
        return {"content": "I'm sorry, I cannot process this request right now."}


class BaseAgent(ABC):
    """Base class cho tất cả các agent trong hệ thống"""
    
    def __init__(self, name: str, prompt_file: str):
        self.name = name
        self.prompt_file = prompt_file
        self.system_prompt = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load system prompt từ file"""
        try:
            with open(f"prompts/agents/{self.prompt_file}", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"You are a helpful {self.name} agent."
    
    @abstractmethod
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Xử lý tin nhắn từ user và trả về response
        
        Args:
            user_message: Tin nhắn từ user
            chat_history: Lịch sử chat
            context: Thông tin bổ sung từ router
            
        Returns:
            Dict chứa response từ agent
        """
        pass
    
    def _call_llm(self, messages: List[Dict]) -> str:
        """Gọi LLM với messages và trả về content"""
        response = chat(messages)
        return response.get("content", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
    
    def _build_messages(self, user_message: str, chat_history: List[Dict]) -> List[Dict]:
        """Xây dựng messages cho LLM"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Thêm lịch sử chat
        for turn in chat_history:
            messages.append({"role": "user", "content": turn.get("user")})
            messages.append({"role": "assistant", "content": turn.get("bot")})
        
        # Thêm tin nhắn hiện tại
        messages.append({"role": "user", "content": user_message})
        
        return messages 