from typing import Dict, List
import json
from .base import BaseAgent


class RouterAgent(BaseAgent):
    """Agent chịu trách nhiệm phân tích và định tuyến yêu cầu đến agent phù hợp"""
    
    def __init__(self):
        super().__init__("Router", "router.md")
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Phân tích tin nhắn và quyết định agent nào sẽ xử lý
        
        Returns:
            {
                "target_agent": "tên_agent",
                "reason": "lý do chọn agent này",
                "confidence": 0.95,
                "extracted_info": {...}
            }
        """
        messages = self._build_messages(user_message, chat_history)
        response_content = self._call_llm(messages)
        
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            # Fallback nếu LLM không trả về JSON hợp lệ
            return {
                "target_agent": "faq",
                "reason": "Không thể phân tích yêu cầu, chuyển sang FAQ agent",
                "confidence": 0.3
            } 