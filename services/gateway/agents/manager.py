from typing import Dict, List, Optional
from .router import RouterAgent
from .greeting import GreetingAgent
from .technical import TechnicalAgent
from .faq import FAQAgent
from .lead_agent import LeadAgent
from .smart_lead_agent import SmartLeadAgent
from .action_executor import ActionExecutorAgent
from .critic import CriticAgent
import logging
import asyncio

logger = logging.getLogger(__name__)


class SmartAgentManager:
    """
    Smart Agent Manager sử dụng SmartLeadAgent làm orchestrator chính
    Thông minh hơn, tự nhiên hơn, ít cứng nhắc hơn
    """
    
    def __init__(self):
        # Smart Lead Agent - trợ lý chính thông minh
        self.smart_lead = SmartLeadAgent()
        
        # Các chuyên gia cụ thể
        self.specialists = {
            "technical": TechnicalAgent(),
            "faq": FAQAgent(), 
            "action_executor": ActionExecutorAgent(),
            "greeting": GreetingAgent(),
            "critic": CriticAgent()
        }
        
        # Session memory
        self.session_memory: Dict[str, Dict] = {}
    
    async def process_message(self, user_message: str, chat_history: List[Dict], 
                            session_id: str = None, student_id: str = None) -> Dict:
        """
        Xử lý tin nhắn thông minh với SmartLeadAgent
        """
        try:
            # Chuẩn bị context
            context = {
                "session_id": session_id,
                "student_id": student_id,
                "session_memory": self.session_memory.get(session_id, {}),
                "chat_history": chat_history
            }
            
            # Gọi Smart Lead Agent
            response = self.smart_lead.process(user_message, chat_history, context)
            
            # Xử lý theo quyết định của Smart Lead
            if response.get("requires_specialist"):
                # Cần chuyên gia
                return await self._delegate_to_specialist(response, user_message, chat_history, context)
            
            else:
                # Smart Lead đã tự xử lý
                return response
                
        except Exception as e:
            logger.exception("Error in SmartAgentManager.process_message")
            return {
                "reply": "Xin lỗi, mình đang gặp một chút vấn đề kỹ thuật. Bạn có thể thử lại không?",
                "agent": "smart_agent_manager",
                "success": False,
                "error": str(e)
            }
    
    async def _delegate_to_specialist(self, smart_lead_response: Dict, user_message: str, 
                                   chat_history: List[Dict], context: Dict) -> Dict:
        """
        Ủy thác cho chuyên gia theo quyết định của Smart Lead
        """
        target_specialist = smart_lead_response.get("target_agent")
        
        if target_specialist not in self.specialists:
            logger.warning(f"Specialist '{target_specialist}' not found. Fallback to Smart Lead response.")
            return smart_lead_response
        
        try:
            # Gọi chuyên gia
            specialist = self.specialists[target_specialist]
            
            # Enhanced context với thông tin từ Smart Lead
            enhanced_context = context.copy()
            enhanced_context["smart_lead_analysis"] = {
                "delegation_reason": smart_lead_response.get("delegation_reason"),
                "user_intent": smart_lead_response.get("user_intent", ""),
                "smart_lead_explanation": smart_lead_response.get("reply", "")
            }
            
            # Process với chuyên gia
            if hasattr(specialist, 'process') and asyncio.iscoroutinefunction(specialist.process):
                specialist_response = await specialist.process(user_message, chat_history, enhanced_context)
            else:
                specialist_response = specialist.process(user_message, chat_history, enhanced_context)
            
            # Thêm thông tin về delegation
            specialist_response["delegated_by"] = "smart_lead"
            specialist_response["smart_lead_explanation"] = smart_lead_response.get("reply", "")
            
            return specialist_response
            
        except Exception as e:
            logger.exception(f"Error delegating to specialist {target_specialist}")
            # Fallback về Smart Lead response
            smart_lead_response["specialist_error"] = str(e)
            smart_lead_response["reply"] += " (Lưu ý: Có một chút vấn đề kỹ thuật với chuyên gia, nhưng mình vẫn có thể hỗ trợ bạn cơ bản.)"
            return smart_lead_response
    
    def get_available_agents(self) -> List[str]:
        """Lấy danh sách agents có sẵn"""
        return ["smart_lead"] + list(self.specialists.keys())
    
    def get_session_memory(self, session_id: str) -> Dict:
        """Lấy session memory"""
        return self.session_memory.get(session_id, {})
    
    def update_session_memory(self, session_id: str, key: str, value: any) -> None:
        """Cập nhật session memory"""
        if session_id not in self.session_memory:
            self.session_memory[session_id] = {}
        self.session_memory[session_id][key] = value


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
    
    def get_available_agents(self) -> List[str]:
        """Lấy danh sách agents có sẵn"""
        return ["smart_lead"] + list(self.specialists.keys())
    
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
        workflows_cleaned = self.lead_agent.cleanup_completed
        
        return len(to_remove) + workflows_cleaned


# Default Manager - sử dụng Smart approach
class AgentManager(SmartAgentManager):
    """
    AgentManager mặc định sử dụng SmartLeadAgent
    Thông minh, linh hoạt và tự nhiên hơn
    """
    pass


# Keep the original EnhancedAgentManager as is for backward compatibility