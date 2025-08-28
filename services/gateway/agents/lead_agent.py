"""
Lead Agent - Orchestrator cho hệ thống helpdesk
Phân tích yêu cầu, lập kế hoạch, điều phối subagents và tổng hợp kết quả
"""

from typing import Dict, List, Optional, Any
import json
import uuid
import logging
from datetime import datetime
from enum import Enum

from .base import BaseAgent

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStep(dict):
    """Một bước trong kế hoạch thực hiện"""
    def __init__(self, step_id: str, agent_type: str, description: str, 
                 dependencies: List[str] = None, priority: int = 1):
        super().__init__()
        self.update({
            "step_id": step_id,
            "agent_type": agent_type,
            "description": description,
            "dependencies": dependencies or [],
            "priority": priority,
            "status": TaskStatus.PENDING.value,
            "result": None,
            "created_at": datetime.now().isoformat()
        })


class WorkflowPlan:
    """Kế hoạch thực hiện một nhiệm vụ phức tạp"""
    
    def __init__(self, task_id: str, user_request: str):
        self.task_id = task_id
        self.user_request = user_request
        self.steps: List[TaskStep] = []
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.now()
        
    def add_step(self, step: TaskStep) -> None:
        """Thêm bước vào kế hoạch"""
        self.steps.append(step)
    
    def get_ready_steps(self) -> List[TaskStep]:
        """Lấy các bước sẵn sàng thực hiện (dependencies đã hoàn thành)"""
        completed_steps = {s["step_id"] for s in self.steps if s["status"] == TaskStatus.COMPLETED.value}
        
        ready_steps = []
        for step in self.steps:
            if (step["status"] == TaskStatus.PENDING.value and 
                all(dep in completed_steps for dep in step["dependencies"])):
                ready_steps.append(step)
        
        return sorted(ready_steps, key=lambda x: x["priority"], reverse=True)
    
    def mark_completed(self, step_id: str, result: Dict) -> None:
        """Đánh dấu bước hoàn thành"""
        for step in self.steps:
            if step["step_id"] == step_id:
                step["status"] = TaskStatus.COMPLETED.value
                step["result"] = result
                break
    
    def is_completed(self) -> bool:
        """Kiểm tra tất cả bước đã hoàn thành"""
        # Nếu không có bước nào, coi như chưa hoàn thành
        if not self.steps:
            return False
        return all(s["status"] == TaskStatus.COMPLETED.value for s in self.steps)


class LeadAgent(BaseAgent):
    """
    Lead Agent - Orchestrator chính của hệ thống
    Phân tích yêu cầu phức tạp, lập kế hoạch chi tiết và điều phối các subagents
    """
    
    def __init__(self):
        super().__init__("LeadAgent", "lead_agent.md")
        self.active_workflows: Dict[str, WorkflowPlan] = {}
        self.memory: Dict[str, Any] = {}  # Long-term memory
        
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Xử lý yêu cầu từ user với khả năng lập kế hoạch và điều phối
        """
        try:
            # Đảm bảo context là dict
            if context is None:
                context = {}
            
            # 1. Phân tích độ phức tạp yêu cầu
            complexity_analysis = self._analyze_complexity(user_message, chat_history)
            
            # Lưu complexity_analysis vào context để các method khác sử dụng
            context["complexity_analysis"] = complexity_analysis
            
            if complexity_analysis["is_simple"]:
                # Yêu cầu đơn giản -> routing trực tiếp
                return self._handle_simple_request(user_message, chat_history, context)
            else:
                # Yêu cầu phức tạp -> tạo workflow
                return self._handle_complex_request(user_message, chat_history, context, complexity_analysis)
                
        except Exception as e:
            logger.exception("Error in LeadAgent.process")
            return self._create_error_response(str(e))
    
    def _analyze_complexity(self, user_message: str, chat_history: List[Dict]) -> Dict:
        """Phân tích độ phức tạp của yêu cầu"""
        
        # Quick check cho greeting messages TRƯỚC KHI gọi LLM
        greeting_keywords = [
            "xin chào", "chào", "hello", "hi", "alo", "good morning", 
            "good afternoon", "good evening", "hey", "hế lô", "chào bạn"
        ]
        
        message_lower = user_message.lower().strip()
        
        # Nếu là greeting đơn giản, return ngay
        if any(keyword in message_lower for keyword in greeting_keywords):
            if len(message_lower.split()) <= 3:  # Greeting ngắn
                return {
                    "is_simple": True,
                    "complexity_level": "simple",
                    "required_agents": ["greeting"],
                    "needs_planning": False,
                    "estimated_steps": 1,
                    "reasoning": "Simple greeting message detected"
                }
        
        # Sử dụng LLM để phân tích chi tiết hơn
        analysis_prompt = f"""
        Phân tích yêu cầu sau và xác định độ phức tạp. Trả về CHÍNH XÁC format JSON sau:

        YÊU CẦU: {user_message}

        {{
            "is_simple": true,
            "complexity_level": "simple",
            "required_agents": ["faq"],
            "needs_planning": false,
            "estimated_steps": 1,
            "reasoning": "Lý do phân tích"
        }}

        Tiêu chí phân loại:
        - SIMPLE: Chào hỏi, câu hỏi FAQ đơn giản → is_simple: true
        - MODERATE: Cần tool call hoặc 2-3 bước → is_simple: false  
        - COMPLEX: Nhiều bước phức tạp → is_simple: false

        CHỈ trả về JSON, không thêm text nào khác!
        """
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = self._call_llm(messages)
        
        # Cải thiện parsing với nhiều cách thử
        try:
            # Thử parse trực tiếp
            return json.loads(response.strip())
        except json.JSONDecodeError:
            try:
                # Thử tìm JSON trong response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            logger.warning("Failed to parse complexity analysis, using rule-based analysis")
            return self._rule_based_complexity_analysis(user_message)
    
    def _handle_simple_request(self, user_message: str, chat_history: List[Dict], context: Dict) -> Dict:
        """Xử lý yêu cầu đơn giản bằng routing trực tiếp"""
        
        # Đảm bảo context là dict
        if context is None:
            context = {}
        
        # Lấy thông tin từ complexity analysis
        complexity_analysis = context.get("complexity_analysis", {})
        suggested_agents = complexity_analysis.get("required_agents", ["faq"])
        target_agent = suggested_agents[0] if suggested_agents else "faq"
        
        # Fallback routing logic nếu cần
        valid_agents = ["greeting", "technical", "faq"]
        if target_agent not in valid_agents:
            target_agent = "faq"
        
        return {
            "reply": f"Đã chuyển yêu cầu đến {target_agent} agent",
            "agent": "lead_agent",
            "routing_info": {
                "target_agent": target_agent,
                "reason": complexity_analysis.get("reasoning", "Rule-based routing"),
                "confidence": 0.9
            },
            "workflow_type": "simple_routing"
        }
    
    def _handle_complex_request(self, user_message: str, chat_history: List[Dict], 
                              context: Dict, complexity_analysis: Dict) -> Dict:
        """Xử lý yêu cầu phức tạp bằng workflow planning"""
        
        task_id = str(uuid.uuid4())
        
        # 1. Tạo kế hoạch chi tiết
        workflow_plan = self._create_workflow_plan(task_id, user_message, complexity_analysis)
        
        # 2. Lưu vào active workflows
        self.active_workflows[task_id] = workflow_plan
        
        # 3. Bắt đầu thực hiện
        execution_result = self._execute_workflow(workflow_plan, chat_history, context)
        
        return {
            "reply": execution_result["summary"],
            "agent": "lead_agent",
            "workflow_id": task_id,
            "workflow_type": "complex_planning",
            "execution_details": execution_result["details"],
            "complexity_analysis": complexity_analysis
        }
    
    def _create_workflow_plan(self, task_id: str, user_request: str, complexity_analysis: Dict) -> WorkflowPlan:
        """Tạo kế hoạch workflow cho yêu cầu phức tạp"""
        
        plan = WorkflowPlan(task_id, user_request)
        
        # Sử dụng LLM để tạo kế hoạch chi tiết
        planning_prompt = f"""
        Tạo kế hoạch thực hiện cho yêu cầu: {user_request}
        
        Phân tích độ phức tạp: {json.dumps(complexity_analysis, ensure_ascii=False)}
        
        Các agents có sẵn: greeting, technical, faq, action_executor
        Các tools có sẵn: reset_password, renew_library_card, book_room, create_glpi_ticket, request_dorm_fix
        
        Trả về JSON danh sách các bước:
        {{
            "steps": [
                {{
                    "step_id": "step_1",
                    "agent_type": "faq",
                    "description": "Tìm kiếm thông tin chính sách",
                    "dependencies": [],
                    "priority": 3,
                    "expected_output": "thông tin policy"
                }},
                {{
                    "step_id": "step_2", 
                    "agent_type": "action_executor",
                    "description": "Thực hiện reset password",
                    "dependencies": ["step_1"],
                    "priority": 2,
                    "tool_call": "reset_password"
                }}
            ]
        }}
        """
        
        messages = [{"role": "user", "content": planning_prompt}]
        response = self._call_llm(messages)
        
        try:
            plan_data = json.loads(response)
            for step_data in plan_data.get("steps", []):
                step = TaskStep(
                    step_id=step_data["step_id"],
                    agent_type=step_data["agent_type"],
                    description=step_data["description"],
                    dependencies=step_data.get("dependencies", []),
                    priority=step_data.get("priority", 1)
                )
                # Thêm metadata bổ sung
                if "tool_call" in step_data:
                    step["tool_call"] = step_data["tool_call"]
                if "expected_output" in step_data:
                    step["expected_output"] = step_data["expected_output"]
                
                plan.add_step(step)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse workflow plan, creating fallback")
            # Tạo plan fallback đơn giản
            step = TaskStep("fallback_1", "faq", "Xử lý yêu cầu bằng FAQ agent")
            plan.add_step(step)
        
        return plan
    
    def _execute_workflow(self, plan: WorkflowPlan, chat_history: List[Dict], context: Dict) -> Dict:
        """Thực hiện workflow theo kế hoạch"""
        
        execution_details = []
        
        while not plan.is_completed():
            ready_steps = plan.get_ready_steps()
            
            if not ready_steps:
                break  # Không còn bước nào có thể thực hiện
            
            # Thực hiện bước đầu tiên (priority cao nhất)
            current_step = ready_steps[0]
            current_step["status"] = TaskStatus.IN_PROGRESS.value
            
            logger.info(f"Executing step: {current_step['step_id']} - {current_step['description']}")
            
            # Gọi agent hoặc tool tương ứng
            step_result = self._execute_step(current_step, plan.context, chat_history)
            
            # Cập nhật kết quả
            plan.mark_completed(current_step["step_id"], step_result)
            
            # Cập nhật context để các bước sau sử dụng
            plan.context.update(step_result.get("context_updates", {}))
            
            execution_details.append({
                "step_id": current_step["step_id"],
                "description": current_step["description"],
                "result": step_result
            })
        
        # Tổng hợp kết quả cuối cùng
        final_summary = self._synthesize_results(plan, execution_details)
        
        return {
            "summary": final_summary,
            "details": execution_details
        }
    
    def _execute_step(self, step: TaskStep, workflow_context: Dict, chat_history: List[Dict]) -> Dict:
        """Thực hiện một bước cụ thể"""
        
        agent_type = step["agent_type"]
        
        try:
            if agent_type == "action_executor":
                # Thực hiện tool call
                tool_name = step.get("tool_call")
                if tool_name:
                    return self._execute_tool_call(tool_name, step, workflow_context)
                else:
                    return {"success": False, "error": "No tool specified for action_executor"}
            
            elif agent_type in ["faq", "technical", "greeting"]:
                # Gọi agent tương ứng (giả lập, thực tế sẽ gọi qua AgentManager)
                return self._delegate_to_agent(agent_type, step["description"], chat_history, workflow_context)
            
            else:
                return {"success": False, "error": f"Unknown agent type: {agent_type}"}
                
        except Exception as e:
            logger.exception(f"Error executing step {step['step_id']}")
            return {"success": False, "error": str(e)}
    
    def _execute_tool_call(self, tool_name: str, step: TaskStep, context: Dict) -> Dict:
        """Thực hiện tool call (sẽ tích hợp với Action service)"""
        
        # TODO: Tích hợp với Action service thực tế
        # Hiện tại chỉ mock
        return {
            "success": True,
            "tool_name": tool_name,
            "message": f"Successfully executed {tool_name}",
            "context_updates": {
                f"{tool_name}_executed": True
            }
        }
    
    def _delegate_to_agent(self, agent_type: str, description: str, chat_history: List[Dict], context: Dict) -> Dict:
        """Ủy thác công việc cho agent chuyên trách"""
        
        # TODO: Tích hợp với AgentManager thực tế
        # Hiện tại chỉ mock
        return {
            "success": True,
            "agent": agent_type,
            "response": f"Agent {agent_type} đã xử lý: {description}",
            "context_updates": {
                f"{agent_type}_consulted": True
            }
        }
    
    def _synthesize_results(self, plan: WorkflowPlan, execution_details: List[Dict]) -> str:
        """Tổng hợp kết quả từ tất cả các bước"""
        
        synthesis_prompt = f"""
        Tổng hợp kết quả từ workflow đã thực hiện:
        
        YÊU CẦU GỐC: {plan.user_request}
        
        CÁC BƯỚC ĐÃ THỰC HIỆN:
        {json.dumps(execution_details, ensure_ascii=False, indent=2)}
        
        Hãy tạo một phản hồi tóm tắt ngắn gọn và hữu ích cho người dùng.
        """
        
        messages = [{"role": "user", "content": synthesis_prompt}]
        response = self._call_llm(messages)
        
        return response or "Đã hoàn thành xử lý yêu cầu của bạn."
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Tạo response khi gặp lỗi"""
        return {
            "reply": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.",
            "agent": "lead_agent",
            "error": error_message,
            "workflow_type": "error"
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Lấy trạng thái của một workflow"""
        if workflow_id in self.active_workflows:
            plan = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "user_request": plan.user_request,
                "created_at": plan.created_at.isoformat(),
                "is_completed": plan.is_completed(),
                "steps": plan.steps,
                "context": plan.context
            }
        return None
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Dọn dẹp các workflow đã hoàn thành quá lâu"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for workflow_id, plan in self.active_workflows.items():
            if (plan.is_completed() and 
                plan.created_at.timestamp() < cutoff_time):
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.active_workflows[workflow_id]
        
        return len(to_remove)
    
    def _rule_based_complexity_analysis(self, user_message: str) -> Dict:
        """Rule-based fallback cho complexity analysis"""
        
        message_lower = user_message.lower()
        
        # Simple patterns
        simple_patterns = [
            "xin chào", "chào", "hello", "hi", "alo",
            "cảm ơn", "thanks", "bye", "tạm biệt"
        ]
        
        # Tool-requiring patterns
        tool_patterns = [
            "đặt lại mật khẩu", "reset password", "quên mật khẩu",
            "gia hạn thẻ", "renew", "library card",
            "đặt phòng", "book room", "booking",
            "tạo ticket", "create ticket", "báo cáo sự cố"
        ]
        
        # Complex patterns (multiple steps)
        complex_patterns = [
            "và", "cùng với", "sau đó", "tiếp theo",
            "vừa", "đồng thời"
        ]
        
        if any(pattern in message_lower for pattern in simple_patterns):
            return {
                "is_simple": True,
                "complexity_level": "simple", 
                "required_agents": ["greeting"],
                "needs_planning": False,
                "estimated_steps": 1,
                "reasoning": "Rule-based: greeting pattern detected"
            }
        
        elif any(pattern in message_lower for pattern in tool_patterns):
            # Check if multiple tools needed
            tool_count = sum(1 for pattern in tool_patterns if pattern in message_lower)
            if tool_count > 1 or any(pattern in message_lower for pattern in complex_patterns):
                return {
                    "is_simple": False,
                    "complexity_level": "complex",
                    "required_agents": ["action_executor", "faq"],
                    "needs_planning": True,
                    "estimated_steps": tool_count + 1,
                    "reasoning": "Rule-based: multiple tools or complex conjunction detected"
                }
            else:
                return {
                    "is_simple": False,
                    "complexity_level": "moderate",
                    "required_agents": ["action_executor"],
                    "needs_planning": True,
                    "estimated_steps": 2,
                    "reasoning": "Rule-based: single tool execution needed"
                }
        
        else:
            # Default to FAQ
            return {
                "is_simple": True,
                "complexity_level": "simple",
                "required_agents": ["faq"],
                "needs_planning": False,
                "estimated_steps": 1,
                "reasoning": "Rule-based: default FAQ routing"
            }
