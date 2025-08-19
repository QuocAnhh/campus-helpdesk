from typing import Dict, List
from .base import BaseAgent


class TechnicalAgent(BaseAgent):
    """Agent xử lý các vấn đề kỹ thuật"""
    
    def __init__(self):
        super().__init__("Technical", "technical.md")
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """Xử lý các yêu cầu hỗ trợ kỹ thuật"""
        messages = self._build_messages(user_message, chat_history)
        reply = self._call_llm(messages)
        
        # Kiểm tra nếu cần thực hiện action cụ thể
        extracted_info = context.get("extracted_info", {}) if context else {}
        needs_action = self._check_needs_action(user_message, extracted_info)
        
        result = {
            "reply": reply,
            "agent": "technical"
        }
        
        if needs_action:
            result["suggested_action"] = needs_action
        
        return result
    
    def _check_needs_action(self, message: str, extracted_info: Dict) -> Dict:
        """Kiểm tra nếu cần thực hiện action cụ thể"""
        message_lower = message.lower()
        
        if "đặt lại mật khẩu" in message_lower or "reset password" in message_lower:
            return {
                "type": "password_reset",
                "description": "Yêu cầu đặt lại mật khẩu"
            }
        
        return None 