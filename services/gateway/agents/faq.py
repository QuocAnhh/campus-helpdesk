from typing import Dict, List
import httpx
import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)


class FAQAgent(BaseAgent):
    """Agent xử lý các câu hỏi thường gặp và thông tin chung"""
    
    def __init__(self):
        super().__init__("FAQ", "faq.md")
        self.policy_url = "http://policy:8000"  # URL của policy service
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """Xử lý câu hỏi FAQ bằng cách tìm kiếm thông tin từ knowledge base"""
        
        # Tìm kiếm thông tin từ policy service
        relevant_info = self._search_knowledge_base(user_message)
        
        # Xây dựng prompt với thông tin tìm được
        messages = self._build_messages_with_context(user_message, chat_history, relevant_info)
        reply = self._call_llm(messages)
        
        return {
            "reply": reply,
            "agent": "faq",
            "sources": relevant_info.get("sources", []) if relevant_info else []
        }
    
    def _search_knowledge_base(self, query: str) -> Dict:
        """Tìm kiếm thông tin từ knowledge base"""
        try:
            # Gọi policy service để tìm kiếm thông tin
            # Tạm thời return None, sẽ implement sau
            return None
        except Exception as e:
            logger.exception("Error searching knowledge base for query='%s'", query)
            return None
    
    def _build_messages_with_context(self, user_message: str, chat_history: List[Dict], context_info: Dict) -> List[Dict]:
        """Xây dựng messages với thông tin context từ knowledge base"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Thêm context nếu có
        if context_info and context_info.get("citations"):
            context_text = "\n".join([c.get("quote", "") for c in context_info["citations"]])
            context_message = f"THÔNG TIN THAM KHẢO:\n{context_text}\n\n"
            messages.append({"role": "system", "content": context_message})
        
        # Thêm lịch sử chat
        for turn in chat_history:
            messages.append({"role": "user", "content": turn.get("user")})
            messages.append({"role": "assistant", "content": turn.get("bot")})
        
        # Thêm tin nhắn hiện tại
        messages.append({"role": "user", "content": user_message})
        
        return messages