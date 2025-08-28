from typing import Dict, List, Optional
from .router import RouterAgent
from .greeting import GreetingAgent
from .technical import TechnicalAgent
from .faq import FAQAgent
import logging

logger = logging.getLogger(__name__)


class AgentManager:
    """Quản lý tất cả các agent trong hệ thống"""
    
    def __init__(self):
        # Khởi tạo router agent
        self.router = RouterAgent()
        
        # Khởi tạo các agent chuyên biệt
        self.agents = {
            "greeting": GreetingAgent(),
            "technical": TechnicalAgent(),
            "faq": FAQAgent(),
            # Có thể thêm các agent khác ở đây
            # "schedule": ScheduleAgent(),
            # "academic": AcademicAgent(),
            # "financial": FinancialAgent(),
            # "dormitory": DormitoryAgent(),
        }
    
    async def process_message(self, user_message: str, chat_history: List[Dict], session_id: str = None) -> Dict:
        """
        Xử lý tin nhắn từ user thông qua hệ thống multi-agent
        
        Args:
            user_message: Tin nhắn từ user
            chat_history: Lịch sử chat
            session_id: ID phiên chat
            
        Returns:
            Dict chứa response từ agent được chọn
        """
        try:
            # 1. Router phân tích và chọn agent
            routing_result = self.router.process(user_message, chat_history)
            target_agent_name = routing_result.get("target_agent", "faq")
            
            # 2. Kiểm tra agent có tồn tại không
            if target_agent_name not in self.agents:
                logger.warning("Target agent '%s' not found. Falling back to FAQ.", target_agent_name)
                target_agent_name = "faq"  # Fallback to FAQ agent
            
            # 3. Gọi agent được chọn để xử lý
            target_agent = self.agents[target_agent_name]
            response = target_agent.process(user_message, chat_history, routing_result)
            
            # 4. Thêm thông tin routing vào response
            response["routing_info"] = {
                "selected_agent": target_agent_name,
                "reason": routing_result.get("reason", ""),
                "confidence": routing_result.get("confidence", 0.5)
            }
            
            return response
            
        except Exception as e:
            logger.exception("Error in AgentManager.process_message")
            # Fallback response
            return {
                "reply": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Bạn có thể thử lại không?",
                "agent": "error",
                "routing_info": {
                    "selected_agent": "error",
                    "reason": "System error occurred",
                    "confidence": 0.0
                }
            }
    
    def add_agent(self, name: str, agent_instance):
        """Thêm agent mới vào hệ thống"""
        self.agents[name] = agent_instance
    
    def remove_agent(self, name: str):
        """Xóa agent khỏi hệ thống"""
        if name in self.agents:
            del self.agents[name]
    
    def get_available_agents(self) -> List[str]:
        """Lấy danh sách các agent có sẵn"""
        return list(self.agents.keys())