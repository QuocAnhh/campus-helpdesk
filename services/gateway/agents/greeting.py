from typing import Dict, List
from .base import BaseAgent


class GreetingAgent(BaseAgent):
    """Agent xử lý lời chào và trò chuyện phiếm"""
    
    def __init__(self):
        super().__init__("Greeting", "greeting.md")
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """Xử lý lời chào và tạo phản hồi thân thiện"""
        messages = self._build_messages(user_message, chat_history)
        reply = self._call_llm(messages)
        
        return {
            "reply": reply,
            "agent": "greeting"
        } 