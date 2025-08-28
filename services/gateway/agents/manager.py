from typing import Dict, List, Optional
from .router import RouterAgent
from .greeting import GreetingAgent
from .technical import TechnicalAgent
from .faq import FAQAgent
from .lead_agent import LeadAgent
from .action_executor import ActionExecutorAgent
from .critic import CriticAgent
import logging
import asyncio

logger = logging.getLogger(__name__)


class EnhancedAgentManager:
    """
    Enhanced Agent Manager với Lead-Agent orchestration
    Hỗ trợ cả simple routing và complex workflow planning
    """
    
    def __init__(self):
        # Lead Agent - điều phối chính
        self.lead_agent = LeadAgent()
        
        # Các specialized agents
        self.agents = {
            "greeting": GreetingAgent(),
            "technical": TechnicalAgent(), 
            "faq": FAQAgent(),
            "action_executor": ActionExecutorAgent(),
            "critic": CriticAgent()
        }
        
        # Router agent (backup cho simple routing)
        self.router = RouterAgent()
        
        # Memory và state management
        self.session_memory: Dict[str, Dict] = {}
        self.global_memory: Dict[str, any] = {}
    
    async def process_message(self, user_message: str, chat_history: List[Dict], 
                            session_id: str = None, student_id: str = None) -> Dict:
        """
        Xử lý tin nhắn với Lead-Agent orchestration
        """
        try:
            # 1. Chuẩn bị context
            context = self._prepare_context(session_id, student_id, chat_history)
            
            # 2. Gọi Lead Agent để xử lý
            response = self.lead_agent.process(user_message, chat_history, context)
            
            # 3. Xử lý theo loại workflow
            if response.get("workflow_type") == "simple_routing":
                # Simple routing - ủy thác cho agent cụ thể
                return await self._handle_simple_routing(response, user_message, chat_history, context)
            
            elif response.get("workflow_type") == "complex_planning":
                # Complex workflow - đã được Lead Agent xử lý
                return response
            
            else:
                # Error hoặc fallback
                return response
                
        except Exception as e:
            logger.exception("Error in EnhancedAgentManager.process_message")
            return self._create_fallback_response(user_message, str(e))
    
    async def _handle_simple_routing(self, lead_response: Dict, user_message: str, 
                                   chat_history: List[Dict], context: Dict) -> Dict:
        """Xử lý simple routing - ủy thác cho agent cụ thể"""
        
        routing_info = lead_response.get("routing_info", {})
        target_agent_name = routing_info.get("target_agent", "faq")
        
        # Kiểm tra agent có tồn tại không
        if target_agent_name not in self.agents:
            logger.warning(f"Target agent '{target_agent_name}' not found. Using FAQ.")
            target_agent_name = "faq"
        
        # Gọi agent được chọn
        target_agent = self.agents[target_agent_name]
        
        # Xử lý async nếu cần (cho ActionExecutor)
        if hasattr(target_agent, 'process') and asyncio.iscoroutinefunction(target_agent.process):
            agent_response = await target_agent.process(user_message, chat_history, context)
        else:
            agent_response = target_agent.process(user_message, chat_history, context)
        
        # Thêm routing info vào response
        agent_response["routing_info"] = routing_info
        agent_response["orchestrated_by"] = "lead_agent"
        
        return agent_response
    
    def _prepare_context(self, session_id: str, student_id: str, chat_history: List[Dict]) -> Dict:
        """Chuẩn bị context cho việc xử lý"""
        
        context = {
            "session_id": session_id,
            "student_id": student_id,
            "session_context": self.session_memory.get(session_id, {}),
            "global_context": self.global_memory,
            "chat_length": len(chat_history)
        }
        
        # Trích xuất thông tin từ chat history
        if chat_history:
            last_interaction = chat_history[-1]
            context["last_agent"] = last_interaction.get("agent", "unknown")
            context["conversation_flow"] = self._analyze_conversation_flow(chat_history)
        
        return context
    
    def _analyze_conversation_flow(self, chat_history: List[Dict]) -> Dict:
        """Phân tích luồng hội thoại để hiểu context"""
        
        if not chat_history:
            return {"type": "new_conversation"}
        
        # Đếm số lượng tương tác với mỗi agent
        agent_interactions = {}
        for turn in chat_history:
            agent = turn.get("agent", "unknown")
            agent_interactions[agent] = agent_interactions.get(agent, 0) + 1
        
        # Xác định pattern
        if len(chat_history) == 1:
            return {"type": "initial_request"}
        elif len(chat_history) <= 3:
            return {"type": "short_conversation", "dominant_agent": max(agent_interactions, key=agent_interactions.get)}
        else:
            return {"type": "extended_conversation", "agent_distribution": agent_interactions}
    
    def update_session_memory(self, session_id: str, key: str, value: any) -> None:
        """Cập nhật session memory"""
        if session_id not in self.session_memory:
            self.session_memory[session_id] = {}
        self.session_memory[session_id][key] = value
    
    def get_session_memory(self, session_id: str) -> Dict:
        """Lấy session memory"""
        return self.session_memory.get(session_id, {})
    
    async def evaluate_response_quality(self, response: Dict, original_request: str, 
                                      context: Dict) -> Dict:
        """Đánh giá chất lượng response bằng Critic Agent"""
        
        evaluation_context = {
            "response_to_evaluate": response,
            "original_request": original_request,
            **context
        }
        
        return self.agents["critic"].process(
            user_message=original_request,
            chat_history=[],
            context=evaluation_context
        )
    
    def _create_fallback_response(self, user_message: str, error: str) -> Dict:
        """Tạo fallback response khi có lỗi"""
        return {
            "reply": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Bạn có thể thử lại không?",
            "agent": "enhanced_manager",
            "error": error,
            "fallback": True
        }
    
    def get_available_agents(self) -> List[str]:
        """Lấy danh sách agents có sẵn"""
        return ["lead_agent"] + list(self.agents.keys())
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Lấy trạng thái workflow từ Lead Agent"""
        return self.lead_agent.get_workflow_status(workflow_id)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Dọn dẹp session memory cũ"""
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for session_id, session_data in self.session_memory.items():
            last_activity = session_data.get("last_activity")
            if last_activity and datetime.fromisoformat(last_activity) < cutoff_time:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.session_memory[session_id]
        
        # Dọn dẹp workflows trong Lead Agent
        workflows_cleaned = self.lead_agent.cleanup_completed_workflows(max_age_hours)
        
        return len(to_remove) + workflows_cleaned


# Backward compatibility
class AgentManager(EnhancedAgentManager):
    """Alias for backward compatibility"""
    pass