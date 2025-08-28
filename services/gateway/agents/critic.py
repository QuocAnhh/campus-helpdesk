"""
Critic Agent - Đánh giá chất lượng và tính đúng đắn của kết quả
Phản biện và đề xuất cải thiện cho các response từ agents khác
"""

from typing import Dict, List, Optional, Any
import json
import logging
from .base import BaseAgent

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Agent chuyên trách đánh giá và phản biện kết quả từ các agents khác"""
    
    def __init__(self):
        super().__init__("Critic", "critic.md")
        self.evaluation_criteria = {
            "accuracy": "Tính chính xác của thông tin",
            "completeness": "Tính đầy đủ của câu trả lời", 
            "relevance": "Mức độ liên quan đến yêu cầu",
            "clarity": "Tính rõ ràng và dễ hiểu",
            "actionability": "Khả năng thực hiện/hành động",
            "safety": "Tính an toàn và tuân thủ quy định"
        }
    
    def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Đánh giá response từ agents khác
        Context phải chứa response cần đánh giá
        """
        try:
            if not context or "response_to_evaluate" not in context:
                return self._create_error_response("Không có response để đánh giá")
            
            response_to_evaluate = context["response_to_evaluate"]
            original_request = context.get("original_request", user_message)
            
            # Thực hiện đánh giá
            evaluation_result = self._evaluate_response(
                original_request, response_to_evaluate, context
            )
            
            # Tạo feedback và đề xuất cải thiện
            improvement_suggestions = self._generate_improvement_suggestions(
                evaluation_result, response_to_evaluate, original_request
            )
            
            return {
                "reply": self._format_evaluation_summary(evaluation_result, improvement_suggestions),
                "agent": "critic",
                "evaluation": evaluation_result,
                "improvement_suggestions": improvement_suggestions,
                "overall_quality": evaluation_result["overall_score"]
            }
            
        except Exception as e:
            logger.exception("Error in CriticAgent.process")
            return self._create_error_response(str(e))
    
    def _evaluate_response(self, original_request: str, response: Dict, context: Dict) -> Dict:
        """Đánh giá chi tiết response theo các tiêu chí"""
        
        evaluation_prompt = f"""
        Đánh giá response sau theo các tiêu chí chất lượng:
        
        YÊU CẦU GỐC: {original_request}
        
        RESPONSE CẦN ĐÁNH GIÁ:
        {json.dumps(response, ensure_ascii=False, indent=2)}
        
        CONTEXT BỔ SUNG:
        {json.dumps(context, ensure_ascii=False, indent=2)}
        
        TIÊU CHÍ ĐÁNH GIÁ:
        {json.dumps(self.evaluation_criteria, ensure_ascii=False, indent=2)}
        
        Hãy đánh giá theo từng tiêu chí và trả về JSON:
        {{
            "scores": {{
                "accuracy": 8.5,
                "completeness": 7.0,
                "relevance": 9.0,
                "clarity": 8.0,
                "actionability": 6.5,
                "safety": 9.5
            }},
            "overall_score": 8.1,
            "strengths": [
                "Câu trả lời chính xác và phù hợp",
                "Thông tin đầy đủ và chi tiết"
            ],
            "weaknesses": [
                "Thiếu hướng dẫn cụ thể cho việc thực hiện",
                "Có thể rút gọn để dễ hiểu hơn"
            ],
            "critical_issues": [
                "Không có vấn đề nghiêm trọng nào"
            ]
        }}
        
        Thang điểm: 0-10 (10 là tốt nhất)
        """
        
        messages = [{"role": "user", "content": evaluation_prompt}]
        response_text = self._call_llm(messages)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse evaluation result")
            return self._create_fallback_evaluation(response)
    
    def _create_fallback_evaluation(self, response: Dict) -> Dict:
        """Tạo đánh giá fallback khi LLM không trả về JSON hợp lệ"""
        
        # Đánh giá cơ bản dựa trên structure của response
        scores = {}
        
        # Accuracy: Có thông tin cụ thể không?
        scores["accuracy"] = 7.0 if response.get("reply") and len(response["reply"]) > 50 else 5.0
        
        # Completeness: Response có đầy đủ thông tin không?
        scores["completeness"] = 7.0 if "agent" in response and "reply" in response else 5.0
        
        # Relevance: Mặc định trung bình
        scores["relevance"] = 6.5
        
        # Clarity: Dựa trên độ dài và cấu trúc
        reply_length = len(response.get("reply", ""))
        scores["clarity"] = 8.0 if 50 <= reply_length <= 500 else 6.0
        
        # Actionability: Có suggested_action không?
        scores["actionability"] = 8.0 if "suggested_action" in response else 5.0
        
        # Safety: Mặc định cao (không có nội dung nhạy cảm)
        scores["safety"] = 9.0
        
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            "scores": scores,
            "overall_score": round(overall_score, 1),
            "strengths": ["Response có cấu trúc cơ bản"],
            "weaknesses": ["Không thể đánh giá chi tiết do lỗi parse"],
            "critical_issues": []
        }
    
    def _generate_improvement_suggestions(self, evaluation: Dict, response: Dict, original_request: str) -> List[Dict]:
        """Tạo đề xuất cải thiện dựa trên kết quả đánh giá"""
        
        suggestions = []
        scores = evaluation.get("scores", {})
        
        # Đề xuất cải thiện cho từng tiêu chí điểm thấp
        for criterion, score in scores.items():
            if score < 7.0:  # Threshold cho điểm thấp
                suggestion = self._get_improvement_suggestion(criterion, score, response, original_request)
                if suggestion:
                    suggestions.append(suggestion)
        
        # Đề xuất từ critical issues
        critical_issues = evaluation.get("critical_issues", [])
        for issue in critical_issues:
            if issue != "Không có vấn đề nghiêm trọng nào":
                suggestions.append({
                    "type": "critical_fix",
                    "priority": "high",
                    "description": f"Khắc phục vấn đề nghiêm trọng: {issue}",
                    "specific_action": self._get_critical_fix_action(issue)
                })
        
        return suggestions
    
    def _get_improvement_suggestion(self, criterion: str, score: float, response: Dict, original_request: str) -> Optional[Dict]:
        """Tạo đề xuất cải thiện cho một tiêu chí cụ thể"""
        
        suggestion_map = {
            "accuracy": {
                "description": "Cải thiện tính chính xác thông tin",
                "specific_action": "Kiểm tra lại thông tin với nguồn đáng tin cậy và bổ sung chi tiết cụ thể",
                "priority": "high" if score < 5.0 else "medium"
            },
            "completeness": {
                "description": "Bổ sung thông tin thiếu sót",
                "specific_action": "Thêm thông tin về quy trình, thời gian, và các yêu cầu cần thiết",
                "priority": "medium"
            },
            "relevance": {
                "description": "Tăng mức độ liên quan đến yêu cầu",
                "specific_action": "Tập trung vào các khía cạnh trực tiếp liên quan đến câu hỏi của người dùng",
                "priority": "high"
            },
            "clarity": {
                "description": "Cải thiện tính rõ ràng và dễ hiểu",
                "specific_action": "Sử dụng ngôn ngữ đơn giản hơn và cấu trúc câu trả lời có logic",
                "priority": "medium"
            },
            "actionability": {
                "description": "Tăng khả năng thực hiện hành động",
                "specific_action": "Cung cấp các bước thực hiện cụ thể và rõ ràng",
                "priority": "high" if "technical" in response.get("agent", "") else "medium"
            },
            "safety": {
                "description": "Đảm bảo tính an toàn và tuân thủ quy định",
                "specific_action": "Kiểm tra lại các thông tin nhạy cảm và tuân thủ chính sách bảo mật",
                "priority": "high"
            }
        }
        
        if criterion in suggestion_map:
            suggestion_info = suggestion_map[criterion]
            return {
                "type": "improvement",
                "criterion": criterion,
                "current_score": score,
                "priority": suggestion_info["priority"],
                "description": suggestion_info["description"],
                "specific_action": suggestion_info["specific_action"]
            }
        
        return None
    
    def _get_critical_fix_action(self, issue: str) -> str:
        """Tạo hành động khắc phục cho vấn đề nghiêm trọng"""
        
        if "bảo mật" in issue.lower() or "security" in issue.lower():
            return "Xem xét lại và loại bỏ thông tin nhạy cảm, áp dụng các biện pháp bảo mật phù hợp"
        elif "sai lệch" in issue.lower() or "incorrect" in issue.lower():
            return "Kiểm tra lại thông tin với nguồn chính thức và sửa đổi nội dung sai lệch"
        elif "chính sách" in issue.lower() or "policy" in issue.lower():
            return "Đảm bảo tuân thủ đúng chính sách và quy định của trường"
        else:
            return f"Khắc phục ngay vấn đề: {issue}"
    
    def _format_evaluation_summary(self, evaluation: Dict, suggestions: List[Dict]) -> str:
        """Tạo tóm tắt đánh giá dễ đọc"""
        
        overall_score = evaluation.get("overall_score", 0)
        scores = evaluation.get("scores", {})
        strengths = evaluation.get("strengths", [])
        weaknesses = evaluation.get("weaknesses", [])
        
        # Xác định mức độ chất lượng
        if overall_score >= 8.5:
            quality_level = "Xuất sắc"
        elif overall_score >= 7.0:
            quality_level = "Tốt"
        elif overall_score >= 5.5:
            quality_level = "Trung bình"
        else:
            quality_level = "Cần cải thiện"
        
        summary = f"**Đánh giá chất lượng response: {quality_level} ({overall_score}/10)**\n\n"
        
        # Chi tiết điểm số
        summary += "**Chi tiết điểm số:**\n"
        for criterion, score in scores.items():
            criterion_name = self.evaluation_criteria.get(criterion, criterion)
            summary += f"- {criterion_name}: {score}/10\n"
        
        # Điểm mạnh
        if strengths:
            summary += f"\n**Điểm mạnh:**\n"
            for strength in strengths:
                summary += f"✓ {strength}\n"
        
        # Điểm yếu
        if weaknesses:
            summary += f"\n**Điểm cần cải thiện:**\n"
            for weakness in weaknesses:
                summary += f"⚠ {weakness}\n"
        
        # Đề xuất cải thiện
        high_priority_suggestions = [s for s in suggestions if s.get("priority") == "high"]
        if high_priority_suggestions:
            summary += f"\n**Đề xuất ưu tiên cao:**\n"
            for suggestion in high_priority_suggestions:
                summary += f"🔥 {suggestion['description']}: {suggestion['specific_action']}\n"
        
        return summary
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Tạo response khi gặp lỗi"""
        return {
            "reply": "Không thể thực hiện đánh giá do lỗi hệ thống.",
            "agent": "critic",
            "error": error_message,
            "evaluation": None
        }
    
    def evaluate_workflow_result(self, workflow_plan: Dict, execution_results: List[Dict], 
                                final_response: str) -> Dict:
        """Đánh giá kết quả của toàn bộ workflow"""
        
        evaluation_prompt = f"""
        Đánh giá kết quả workflow đã thực hiện:
        
        KẾ HOẠCH WORKFLOW:
        {json.dumps(workflow_plan, ensure_ascii=False, indent=2)}
        
        KẾT QUẢ THỰC HIỆN:
        {json.dumps(execution_results, ensure_ascii=False, indent=2)}
        
        RESPONSE CUỐI CÙNG:
        {final_response}
        
        Đánh giá:
        - Workflow có được thực hiện đúng kế hoạch không?
        - Kết quả có đáp ứng mục tiêu ban đầu không?
        - Có bước nào thất bại hoặc không cần thiết không?
        - Hiệu quả tổng thể như thế nào?
        
        Trả về JSON:
        {{
            "workflow_success": true/false,
            "plan_adherence": 0.9,
            "goal_achievement": 0.8,
            "efficiency_score": 0.7,
            "failed_steps": ["step_id_1"],
            "unnecessary_steps": ["step_id_2"],
            "missing_steps": ["bước_thiếu"],
            "overall_assessment": "Tổng quan đánh giá",
            "recommendations": [
                "Đề xuất cải thiện cho lần sau"
            ]
        }}
        """
        
        messages = [{"role": "user", "content": evaluation_prompt}]
        response = self._call_llm(messages)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "workflow_success": True,
                "plan_adherence": 0.5,
                "goal_achievement": 0.5,
                "efficiency_score": 0.5,
                "overall_assessment": "Không thể đánh giá chi tiết do lỗi parse",
                "recommendations": ["Cần cải thiện hệ thống đánh giá"]
            }
