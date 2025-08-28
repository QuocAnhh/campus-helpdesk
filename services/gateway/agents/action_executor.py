"""
Action Executor Agent - Chuyên trách thực hiện các tools/actions
Tích hợp với Action service để thực hiện các công cụ có sẵn
"""

from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
import sys

# Add path for imports
sys.path.append('/app')

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Import httpx with fallback
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available, tool execution will be disabled")


class ActionExecutorAgent(BaseAgent):
    """Agent chuyên trách thực hiện các tools và actions"""
    
    def __init__(self):
        super().__init__("ActionExecutor", "action_executor.md")
        self.action_service_url = "http://action:8000"
        self.available_tools = {
            "reset_password": {
                "description": "Đặt lại mật khẩu cho sinh viên",
                "required_params": ["student_id"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string"}
                    },
                    "required": ["student_id"]
                }
            },
            "renew_library_card": {
                "description": "Gia hạn thẻ thư viện",
                "required_params": ["student_id", "card_number", "duration"],
                "schema": {
                    "type": "object", 
                    "properties": {
                        "student_id": {"type": "string"},
                        "card_number": {"type": "string"},
                        "duration": {"type": "string"}
                    },
                    "required": ["student_id", "card_number", "duration"]
                }
            },
            "book_room": {
                "description": "Đặt phòng học/họp",
                "required_params": ["room_id", "start_time", "end_time"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "room_id": {"type": "string"},
                        "start_time": {"type": "string", "format": "date-time"},
                        "end_time": {"type": "string", "format": "date-time"}
                    },
                    "required": ["room_id", "start_time", "end_time"]
                }
            },
            "create_glpi_ticket": {
                "description": "Tạo ticket trong hệ thống GLPI",
                "required_params": ["title", "description", "category"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "category": {"type": "string"}
                    },
                    "required": ["title", "description", "category"]
                }
            },
            "request_dorm_fix": {
                "description": "Yêu cầu sửa chữa ký túc xá",
                "required_params": ["room_number", "issue_type", "description"],
                "schema": {
                    "type": "object",
                    "properties": {
                        "room_number": {"type": "string"},
                        "issue_type": {"type": "string"},
                        "description": {"type": "string"},
                        "urgency": {"type": "string"}
                    },
                    "required": ["room_number", "issue_type", "description"]
                }
            }
        }
    
    async def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Xử lý yêu cầu thực hiện action/tool
        """
        try:
            # 1. Phân tích yêu cầu để xác định tool cần dùng
            tool_analysis = self._analyze_tool_request(user_message, context)
            
            if not tool_analysis["tool_name"]:
                return self._create_guidance_response()
            
            # 2. Kiểm tra tool có tồn tại không
            tool_name = tool_analysis["tool_name"]
            if tool_name not in self.available_tools:
                return self._create_tool_not_found_response(tool_name)
            
            # 3. Trích xuất tham số
            tool_params = self._extract_tool_parameters(tool_name, user_message, context, tool_analysis)
            
            # 4. Validate tham số
            validation_result = self._validate_parameters(tool_name, tool_params)
            if not validation_result["valid"]:
                return self._create_parameter_error_response(tool_name, validation_result)
            
            # 5. Thực hiện tool call
            execution_result = await self._execute_tool(tool_name, tool_params, context)
            
            # 6. Tạo response
            return self._create_success_response(tool_name, execution_result)
            
        except Exception as e:
            logger.exception("Error in ActionExecutorAgent.process")
            return self._create_error_response(str(e))
    
    def _analyze_tool_request(self, user_message: str, context: Dict = None) -> Dict:
        """Phân tích yêu cầu để xác định tool cần sử dụng"""
        
        # Sử dụng LLM để phân tích intent
        analysis_prompt = f"""
        Phân tích yêu cầu và xác định tool cần sử dụng:
        
        YÊU CẦU: {user_message}
        
        TOOLS CÓ SẴN:
        {json.dumps(list(self.available_tools.keys()), ensure_ascii=False)}
        
        CHI TIẾT TOOLS:
        {self._get_tools_description()}
        
        Context từ workflow: {json.dumps(context or {}, ensure_ascii=False)}
        
        Trả về JSON:
        {{
            "tool_name": "tên_tool_hoặc_null",
            "confidence": 0.95,
            "reasoning": "lý do chọn tool này",
            "extracted_entities": {{
                "student_id": "value_nếu_có",
                "room_number": "value_nếu_có",
                ...
            }}
        }}
        """
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = self._call_llm(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse tool analysis")
            return {
                "tool_name": None,
                "confidence": 0.0,
                "reasoning": "Parse error",
                "extracted_entities": {}
            }
    
    def _get_tools_description(self) -> str:
        """Lấy mô tả chi tiết các tools"""
        descriptions = []
        for tool_name, tool_info in self.available_tools.items():
            descriptions.append(f"- {tool_name}: {tool_info['description']}")
        return "\n".join(descriptions)
    
    def _extract_tool_parameters(self, tool_name: str, user_message: str, 
                                context: Dict, tool_analysis: Dict) -> Dict:
        """Trích xuất tham số cho tool từ user_message và context"""
        
        tool_schema = self.available_tools[tool_name]["schema"]
        extracted_entities = tool_analysis.get("extracted_entities", {})
        
        # Bước 1: Lấy tham số từ extracted_entities
        params = {}
        for param in tool_schema["required"]:
            if param in extracted_entities and extracted_entities[param]:
                params[param] = extracted_entities[param]
        
        # Bước 2: Lấy tham số từ context (workflow context, session context)
        if context:
            # Từ workflow context
            workflow_context = context.get("workflow_context", {})
            for param in tool_schema["required"]:
                if param not in params and param in workflow_context:
                    params[param] = workflow_context[param]
            
            # Từ session context (student_id, etc.)
            session_context = context.get("session_context", {})
            for param in tool_schema["required"]:
                if param not in params and param in session_context:
                    params[param] = session_context[param]
        
        # Bước 3: Sử dụng LLM để trích xuất tham số còn thiếu
        missing_params = [p for p in tool_schema["required"] if p not in params]
        if missing_params:
            params.update(self._extract_missing_parameters(
                tool_name, user_message, missing_params, tool_schema
            ))
        
        return params
    
    def _extract_missing_parameters(self, tool_name: str, user_message: str, 
                                   missing_params: List[str], schema: Dict) -> Dict:
        """Sử dụng LLM để trích xuất tham số còn thiếu"""
        
        extraction_prompt = f"""
        Trích xuất tham số cho tool '{tool_name}' từ yêu cầu người dùng:
        
        YÊU CẦU: {user_message}
        
        CẦN TRÍCH XUẤT: {missing_params}
        
        SCHEMA: {json.dumps(schema, ensure_ascii=False)}
        
        Quy tắc:
        - student_id: mã số sinh viên (thường dạng 2021xxxx)
        - room_number: số phòng (ví dụ: A101, B205)
        - date-time: định dạng ISO (2024-01-15T10:00:00)
        - duration: thời gian (ví dụ: "1 year", "6 months")
        
        Trả về JSON:
        {{
            "param1": "value1",
            "param2": "value2"
        }}
        
        Nếu không tìm thấy tham số nào, trả về null cho tham số đó.
        """
        
        messages = [{"role": "user", "content": extraction_prompt}]
        response = self._call_llm(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to extract missing parameters")
            return {param: None for param in missing_params}
    
    def _validate_parameters(self, tool_name: str, params: Dict) -> Dict:
        """Validate tham số tool"""
        
        schema = self.available_tools[tool_name]["schema"]
        required_params = schema["required"]
        
        # Kiểm tra tham số bắt buộc
        missing_params = []
        for param in required_params:
            if param not in params or params[param] is None:
                missing_params.append(param)
        
        if missing_params:
            return {
                "valid": False,
                "error": "missing_required_parameters",
                "missing_params": missing_params,
                "message": f"Thiếu tham số bắt buộc: {', '.join(missing_params)}"
            }
        
        # Validate định dạng (cơ bản)
        validation_errors = []
        
        # Validate student_id format
        if "student_id" in params:
            student_id = params["student_id"]
            if not (student_id.isdigit() and len(student_id) >= 8):
                validation_errors.append("student_id phải là số có ít nhất 8 chữ số")
        
        # Validate datetime format
        for param, value in params.items():
            if param.endswith("_time") and value:
                try:
                    from datetime import datetime
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    validation_errors.append(f"{param} phải có định dạng datetime hợp lệ (ISO)")
        
        if validation_errors:
            return {
                "valid": False,
                "error": "validation_failed",
                "validation_errors": validation_errors,
                "message": "; ".join(validation_errors)
            }
        
        return {"valid": True}
    
    async def _execute_tool(self, tool_name: str, params: Dict, context: Dict = None) -> Dict:
        """Thực hiện tool call tới Action service"""
        
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "error": "dependency_missing",
                "message": "HTTP client not available"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Chuẩn bị request data
                request_data = {
                    "tool_name": tool_name,
                    "tool_args": params
                }
                
                # Headers (có thể thêm authentication)
                headers = {"Content-Type": "application/json"}
                if context and "student_id" in context:
                    headers["X-Student-ID"] = context["student_id"]
                
                # Gọi Action service
                response = await client.post(
                    f"{self.action_service_url}/call_tool",
                    json=request_data,
                    headers=headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "tool_name": tool_name,
                    "result": result,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            if "httpx" in str(type(e)):
                if "HTTPStatusError" in str(type(e)):
                    logger.error(f"HTTP error calling action service: {e}")
                    return {
                        "success": False,
                        "error": "http_error",
                        "status_code": getattr(e.response, 'status_code', 500),
                        "message": f"Lỗi khi gọi dịch vụ: {getattr(e.response, 'status_code', 500)}"
                    }
                elif "RequestError" in str(type(e)):
                    logger.error(f"Request error calling action service: {e}")
                    return {
                        "success": False,
                        "error": "request_error", 
                        "message": "Không thể kết nối đến dịch vụ thực hiện"
                    }
            
            logger.exception("Unexpected error in tool execution")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": f"Lỗi không xác định: {str(e)}"
            }
    
    def _create_success_response(self, tool_name: str, execution_result: Dict) -> Dict:
        """Tạo response khi thực hiện tool thành công"""
        
        if execution_result["success"]:
            return {
                "reply": f"Đã thực hiện thành công {tool_name}. Kết quả: {execution_result['result'].get('message', 'Hoàn thành')}",
                "agent": "action_executor",
                "tool_executed": tool_name,
                "execution_result": execution_result,
                "success": True
            }
        else:
            return {
                "reply": f"Không thể thực hiện {tool_name}. Lỗi: {execution_result.get('message', 'Lỗi không xác định')}",
                "agent": "action_executor", 
                "tool_attempted": tool_name,
                "execution_result": execution_result,
                "success": False
            }
    
    def _create_guidance_response(self) -> Dict:
        """Tạo response hướng dẫn khi không xác định được tool"""
        
        tools_list = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.available_tools.items()
        ])
        
        return {
            "reply": f"Tôi có thể giúp bạn thực hiện các công việc sau:\n\n{tools_list}\n\nBạn muốn làm gì?",
            "agent": "action_executor",
            "available_tools": list(self.available_tools.keys()),
            "success": False,
            "reason": "tool_not_identified"
        }
    
    def _create_tool_not_found_response(self, tool_name: str) -> Dict:
        """Tạo response khi tool không tồn tại"""
        
        return {
            "reply": f"Xin lỗi, tôi không thể thực hiện '{tool_name}'. Các công cụ có sẵn: {', '.join(self.available_tools.keys())}",
            "agent": "action_executor",
            "requested_tool": tool_name,
            "available_tools": list(self.available_tools.keys()),
            "success": False,
            "reason": "tool_not_found"
        }
    
    def _create_parameter_error_response(self, tool_name: str, validation_result: Dict) -> Dict:
        """Tạo response khi có lỗi tham số"""
        
        return {
            "reply": f"Không thể thực hiện {tool_name}. {validation_result['message']}. Bạn vui lòng cung cấp đầy đủ thông tin.",
            "agent": "action_executor",
            "tool_name": tool_name,
            "validation_error": validation_result,
            "success": False,
            "reason": "parameter_validation_failed"
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Tạo response khi có lỗi system"""
        
        return {
            "reply": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu. Vui lòng thử lại sau.",
            "agent": "action_executor",
            "error": error_message,
            "success": False,
            "reason": "system_error"
        }
    
    def get_available_tools(self) -> Dict[str, Dict]:
        """Lấy danh sách tools có sẵn"""
        return self.available_tools
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """Lấy schema của một tool cụ thể"""
        return self.available_tools.get(tool_name, {}).get("schema")
