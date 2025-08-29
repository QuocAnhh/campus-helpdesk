"""
Smart Lead Agent - Trợ lý chính thông minh của Campus Helpdesk
Có khả năng hiểu ngữ cảnh, quyết định thông minh và trả lời tự nhiên
"""

from typing import Dict, List, Optional, Any
import json
import logging
import re

from .base import BaseAgent

logger = logging.getLogger(__name__)


class SmartLeadAgent(BaseAgent):
    """
    Smart Lead Agent - Trợ lý chính thông minh
    Hiểu ngữ cảnh, quyết định có nên tự trả lời hay chuyển chuyên gia
    """
    
    def __init__(self):
        super().__init__("SmartLead", "smart_lead.md")
        self.available_specialists = {
            "technical": "Chuyên gia kỹ thuật - xử lý vấn đề IT, mật khẩu, hệ thống",
            "faq": "Tư vấn thông tin - trả lời về quy định, chính sách trường", 
            "action_executor": "Trợ lý thực hiện - thực hiện công việc cụ thể",
            "enhanced_rag": "Chuyên gia tìm kiếm - tìm kiếm tài liệu chính thức",
            "greeting": "Trợ lý chào hỏi - tạo không khí thân thiện"
        }
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Xử lý yêu cầu một cách thông minh:
        1. Hiểu ngữ cảnh và ý định
        2. Quyết định tự trả lời hay chuyển chuyên gia
        3. Đưa ra phản hồi tự nhiên và phù hợp
        """
        try:
            if context is None:
                context = {}
            
            # Phân tích ý định và quyết định cách xử lý
            decision = self._make_intelligent_decision(user_message, chat_history, context)
            
            if decision["action"] == "direct_response":
                # Tự trả lời trực tiếp
                return self._create_direct_response(user_message, chat_history, decision)
            
            elif decision["action"] == "delegate_to_specialist":
                # Chuyển cho chuyên gia với giải thích
                return self._create_delegation_response(user_message, decision)
            
            elif decision["action"] == "multi_step_coordination":
                # Xử lý phức tạp nhiều bước
                return self._handle_complex_request(user_message, chat_history, decision)
            
            else:
                # Fallback
                return self._create_direct_response(user_message, chat_history, decision)
                
        except Exception as e:
            logger.exception("Error in SmartLeadAgent.process")
            return {
                "reply": "Xin lỗi, mình gặp một chút vấn đề kỹ thuật. Bạn có thể thử lại hoặc diễn đạt khác không?",
                "agent": "smart_lead",
                "success": False,
                "error": str(e)
            }
    
    def _make_intelligent_decision(self, user_message: str, chat_history: List[Dict], context: Dict) -> Dict:
        """
        Phân tích thông minh để quyết định cách xử lý
        """
        
        # Chuẩn bị prompt thông minh
        analysis_prompt = f"""
        Bạn là Smart Lead Agent của Campus Helpdesk. Hãy phân tích yêu cầu sau và quyết định cách xử lý tốt nhất.

        YÊU CẦU HIỆN TẠI: {user_message}
        
        LỊCH SỬ TRƯỚC ĐÓ: {self._format_chat_history(chat_history[-3:]) if chat_history else "Không có"}
        
        CÁC LỰA CHỌN XỬ LÝ:
        
        1. **direct_response**: Tự trả lời trực tiếp
        - Khi: Câu hỏi tổng quát, thông tin về dịch vụ, hướng dẫn cơ bản
        - Ví dụ: "Campus Helpdesk có những dịch vụ gì?"
        
        2. **delegate_to_specialist**: Chuyển cho chuyên gia cụ thể
        - technical: Vấn đề IT, mật khẩu, hệ thống
        - faq: Quy định, chính sách chi tiết của trường
        - action_executor: Thực hiện công việc cụ thể (đặt phòng, gia hạn...)
        - enhanced_rag: Tìm kiếm tài liệu chính thức
        
        3. **multi_step_coordination**: Nhiều bước phức tạp
        - Khi: Cần nhiều chuyên gia hoặc nhiều công việc
        
        Trả về JSON:
        {{
            "action": "direct_response|delegate_to_specialist|multi_step_coordination",
            "reasoning": "Lý do quyết định này",
            "target_specialist": "tên_chuyên_gia_nếu_cần",
            "confidence": 0.9,
            "user_intent": "Ý định của user",
            "context_understanding": "Hiểu biết về ngữ cảnh"
        }}
        
        HÃY PHÂN TÍCH THÔNG MINH VÀ TRẢ VỀ JSON:
        """
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = self._call_llm(messages)
        
        try:
            # Parse JSON response
            if "```json" in response:
                json_content = response.split("```json")[1].split("```")[0].strip()
            else:
                json_content = response.strip()
            
            return json.loads(json_content)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse decision JSON: {e}")
            # Fallback decision based on keywords
            return self._fallback_decision(user_message)
    
    def _create_direct_response(self, user_message: str, chat_history: List[Dict], decision: Dict) -> Dict:
        """
        Tạo câu trả lời trực tiếp thông minh và tự nhiên
        """
        
        response_prompt = f"""
        Bạn là Smart Lead Agent của Campus Helpdesk. Hãy trả lời trực tiếp câu hỏi sau một cách tự nhiên, thân thiện và hữu ích.

        CÂU HỎI: {user_message}
        
        NGỮ CẢNH: {decision.get('context_understanding', '')}
        
        Ý ĐỊNH CỦA USER: {decision.get('user_intent', '')}
        
        HƯỚNG DẪN TRẢ LỜI:
        - Trả lời tự nhiên, không theo template
        - Cung cấp thông tin hữu ích và cụ thể
        - Đề xuất thêm sự hỗ trợ nếu cần
        - Sử dụng ngôn ngữ thân thiện, gần gũi
        - Độ dài: 2-4 câu, vừa đủ thông tin
        
        TRẢ LỜI:
        """
        
        messages = [{"role": "user", "content": response_prompt}]
        response_content = self._call_llm(messages)
        
        return {
            "reply": response_content.strip(),
            "agent": "smart_lead", 
            "action_taken": "direct_response",
            "decision_reasoning": decision.get("reasoning"),
            "success": True
        }
    
    def _create_delegation_response(self, user_message: str, decision: Dict) -> Dict:
        """
        Tạo response khi cần chuyển cho chuyên gia
        """
        
        target_specialist = decision.get("target_specialist", "faq")
        specialist_desc = self.available_specialists.get(target_specialist, "chuyên gia phù hợp")
        
        delegation_prompt = f"""
        Bạn là Smart Lead Agent. User có yêu cầu cần chuyển cho chuyên gia. Hãy giải thích một cách thân thiện.

        YÊU CẦU: {user_message}
        
        CHUYÊN GIA ĐƯỢC CHỌN: {target_specialist} - {specialist_desc}
        
        LÝ DO: {decision.get('reasoning', '')}
        
        Hãy tạo một lời giải thích ngắn gọn (1-2 câu) về:
        - Tại sao cần chuyên gia này
        - Chuyên gia sẽ giúp được gì
        - Tạo cảm giác an tâm cho user
        
        Ví dụ: "Mình thấy bạn cần hỗ trợ về vấn đề mật khẩu. Để giải quyết nhanh và chính xác nhất, mình sẽ kết nối bạn với chuyên gia kỹ thuật ngay bây giờ."
        
        GIẢI THÍCH:
        """
        
        messages = [{"role": "user", "content": delegation_prompt}]
        explanation = self._call_llm(messages)
        
        return {
            "reply": explanation.strip(),
            "agent": "smart_lead",
            "action_taken": "delegate_to_specialist", 
            "target_agent": target_specialist,
            "delegation_reason": decision.get("reasoning"),
            "requires_specialist": True,
            "success": True
        }
    
    def _handle_complex_request(self, user_message: str, chat_history: List[Dict], decision: Dict) -> Dict:
        """
        Xử lý yêu cầu phức tạp nhiều bước
        """
        
        complex_prompt = f"""
        Bạn là Smart Lead Agent xử lý yêu cầu phức tạp. Hãy phân tích và đưa ra kế hoạch.

        YÊU CẦU PHỨC TẠP: {user_message}
        
        Hãy:
        1. Chia nhỏ thành các bước cụ thể
        2. Xác định chuyên gia nào cần cho từng bước
        3. Giải thích cho user biết sẽ làm gì
        
        Trả lời theo format:
        "Mình hiểu bạn cần [tóm tắt yêu cầu]. Để hỗ trợ bạn hiệu quả nhất, mình sẽ [kế hoạch ngắn gọn]. Đầu tiên, mình sẽ [bước đầu tiên]."
        
        PHẢN HỒI:
        """
        
        messages = [{"role": "user", "content": complex_prompt}]
        response_content = self._call_llm(messages)
        
        return {
            "reply": response_content.strip(),
            "agent": "smart_lead",
            "action_taken": "multi_step_coordination",
            "complexity_level": "high",
            "requires_planning": True,
            "success": True
        }
    
    def _fallback_decision(self, user_message: str) -> Dict:
        """
        Fallback decision khi không parse được JSON
        """
        message_lower = user_message.lower()
        
        # Detect greeting
        if any(word in message_lower for word in ["chào", "hello", "hi", "xin chào"]):
            return {
                "action": "direct_response",
                "reasoning": "Greeting message detected",
                "user_intent": "Chào hỏi",
                "confidence": 0.8
            }
        
        # Detect technical issues
        if any(word in message_lower for word in ["mật khẩu", "password", "đăng nhập", "login"]):
            return {
                "action": "delegate_to_specialist",
                "target_specialist": "technical",
                "reasoning": "Technical issue detected",
                "user_intent": "Hỗ trợ kỹ thuật",
                "confidence": 0.7
            }
        
        # Default to direct response
        return {
            "action": "direct_response", 
            "reasoning": "General inquiry",
            "user_intent": "Thông tin chung",
            "confidence": 0.6
        }
    
    def _format_chat_history(self, history: List[Dict]) -> str:
        """Format chat history for context"""
        if not history:
            return "Không có lịch sử"
        
        formatted = []
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return " | ".join(formatted)
