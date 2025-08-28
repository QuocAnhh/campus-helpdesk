"""
Enhanced RAG Agent - Tích hợp nâng cao với Policy service
Hỗ trợ semantic search, reranking và answer generation
"""

from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
import sys
import re

# Add path for imports
sys.path.append('/app')

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Try to import httpx, fallback if not available
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available, some features will be disabled")


class EnhancedRAGAgent(BaseAgent):
    """Agent RAG nâng cao với khả năng search và answer generation"""
    
    def __init__(self):
        super().__init__("EnhancedRAG", "enhanced_rag.md")
        self.policy_service_url = "http://policy:8000"
        self.search_threshold = 0.7  # Threshold cho độ tương tự
        self.max_citations = 5  # Số citation tối đa
        
    async def process(self, user_message: str, chat_history: List[Dict], context: Dict = None) -> Dict:
        """
        Xử lý yêu cầu bằng RAG với search và generation
        """
        try:
            # 1. Phân tích query và tối ưu hóa search
            optimized_query = await self._optimize_search_query(user_message, chat_history, context)
            
            # 2. Tìm kiếm tài liệu liên quan
            search_results = await self._search_documents(optimized_query)
            
            # 3. Rerank và filter kết quả
            relevant_docs = await self._rerank_and_filter(search_results, user_message, context)
            
            # 4. Generate answer từ tài liệu
            if relevant_docs:
                answer = await self._generate_answer(user_message, relevant_docs, chat_history)
                return self._create_success_response(answer, relevant_docs, optimized_query)
            else:
                return self._create_no_results_response(user_message, optimized_query)
                
        except Exception as e:
            logger.exception("Error in EnhancedRAGAgent.process")
            return self._create_error_response(str(e))
    
    async def _optimize_search_query(self, user_message: str, chat_history: List[Dict], 
                                   context: Dict = None) -> str:
        """Tối ưu hóa query để search hiệu quả hơn"""
        
        optimization_prompt = f"""
        Tối ưu hóa query cho tìm kiếm tài liệu. Trả về CHÍNH XÁC format JSON:

        QUERY GỐC: {user_message}

        {{
            "optimized_query": "query đã tối ưu",
            "key_terms": ["term1", "term2"],
            "search_strategy": "broad",
            "reasoning": "lý do tối ưu hóa"
        }}

        CHỈ trả về JSON, không thêm text nào khác!
        """
        
        messages = [{"role": "user", "content": optimization_prompt}]
        response = self._call_llm(messages)
        
        try:
            # Thử parse JSON
            result = json.loads(response.strip())
            return result.get("optimized_query", user_message)
        except json.JSONDecodeError:
            try:
                # Thử tìm JSON trong response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get("optimized_query", user_message)
            except:
                pass
            
            logger.warning("Failed to parse query optimization, using rule-based optimization")
            return self._rule_based_query_optimization(user_message)
    
    def _rule_based_query_optimization(self, user_message: str) -> str:
        """Rule-based query optimization khi LLM fail"""
        # Simple keyword expansion
        query = user_message.lower()
        
        # Expand common terms
        expansions = {
            "học phí": "học phí tuition fee payment",
            "thẻ thư viện": "thẻ thư viện library card renewal",
            "ký túc xá": "ký túc xá dormitory accommodation",
            "đăng ký": "đăng ký registration enrollment",
            "thi": "thi exam examination schedule",
            "điểm": "điểm score grade transcript"
        }
        
        for term, expanded in expansions.items():
            if term in query:
                return expanded
        
        return user_message
    
    async def _search_documents(self, query: str) -> List[Dict]:
        """Tìm kiếm tài liệu từ Policy service"""
        
        if not HTTPX_AVAILABLE:
            logger.error("httpx not available, cannot search documents")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # Gọi policy service để tìm kiếm
                response = await client.post(
                    f"{self.policy_service_url}/rag_answer",
                    json={"text": query},
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Trả về citations từ policy service
                return result.get("citations", [])
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def _rerank_and_filter(self, search_results: List[Dict], user_message: str, 
                               context: Dict = None) -> List[Dict]:
        """Rerank và filter kết quả search"""
        
        if not search_results:
            return []
        
        # Sử dụng LLM để rerank based on relevance
        rerank_prompt = f"""
        Rerank và đánh giá độ liên quan của các tài liệu tìm được:
        
        QUERY: {user_message}
        
        TÀI LIỆU TÌM ĐƯỢC:
        {json.dumps(search_results, ensure_ascii=False, indent=2)}
        
        Hãy đánh giá và sắp xếp lại theo độ liên quan, trả về JSON:
        {{
            "ranked_documents": [
                {{
                    "document_id": "id_hoặc_index", 
                    "relevance_score": 0.95,
                    "relevance_reason": "lý do liên quan",
                    "original_doc": {{...}}
                }}
            ],
            "filtering_reason": "lý do filter"
        }}
        
        Chỉ giữ lại tài liệu có relevance_score >= {self.search_threshold}
        Tối đa {self.max_citations} tài liệu
        """
        
        messages = [{"role": "user", "content": rerank_prompt}]
        response = self._call_llm(messages)
        
        try:
            rerank_result = json.loads(response)
            ranked_docs = rerank_result.get("ranked_documents", [])
            
            # Filter theo threshold và limit
            filtered_docs = [
                doc for doc in ranked_docs 
                if doc.get("relevance_score", 0) >= self.search_threshold
            ][:self.max_citations]
            
            # Trả về original documents
            return [doc.get("original_doc", doc) for doc in filtered_docs]
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse rerank result, using original order")
            return search_results[:self.max_citations]
    
    async def _generate_answer(self, user_message: str, relevant_docs: List[Dict], 
                             chat_history: List[Dict]) -> str:
        """Generate answer từ tài liệu tìm được"""
        
        # Chuẩn bị context từ documents
        doc_context = ""
        for i, doc in enumerate(relevant_docs):
            doc_text = doc.get("quote", doc.get("content", ""))
            source = doc.get("source", f"Document {i+1}")
            doc_context += f"\n[{source}]: {doc_text}\n"
        
        generation_prompt = f"""
        Dựa trên các tài liệu tham khảo, hãy trả lời câu hỏi của sinh viên một cách chính xác và hữu ích.
        
        CÂU HỎI: {user_message}
        
        TÀI LIỆU THAM KHẢO:
        {doc_context}
        
        LỊCH SỬ CHAT:
        {json.dumps(chat_history[-3:] if chat_history else [], ensure_ascii=False)}
        
        YÊU CẦU:
        - Trả lời chính xác dựa trên tài liệu
        - Ngôn ngữ thân thiện, dễ hiểu
        - Trích dẫn nguồn khi cần thiết
        - Nếu tài liệu không đủ thông tin, hãy nói rõ
        - Đưa ra hướng dẫn cụ thể nếu có thể
        
        KHÔNG được tự bịa thông tin không có trong tài liệu tham khảo.
        """
        
        messages = [{"role": "user", "content": generation_prompt}]
        return self._call_llm(messages)
    
    def _create_success_response(self, answer: str, relevant_docs: List[Dict], 
                               optimized_query: str) -> Dict:
        """Tạo response thành công với answer và sources"""
        
        # Tạo danh sách sources
        sources = []
        for doc in relevant_docs:
            source_info = {
                "quote": doc.get("quote", "")[:200] + "..." if len(doc.get("quote", "")) > 200 else doc.get("quote", ""),
                "source": doc.get("source", "Unknown"),
                "relevance": doc.get("relevance_score", 0.8)
            }
            sources.append(source_info)
        
        return {
            "reply": answer,
            "agent": "enhanced_rag",
            "sources": sources,
            "search_info": {
                "original_query": optimized_query,
                "documents_found": len(relevant_docs),
                "search_success": True
            }
        }
    
    def _create_no_results_response(self, user_message: str, optimized_query: str) -> Dict:
        """Tạo response khi không tìm thấy tài liệu liên quan"""
        
        fallback_answer = f"""
        Xin lỗi, tôi không tìm thấy thông tin cụ thể về "{user_message}" trong cơ sở dữ liệu chính sách hiện tại.
        
        Bạn có thể:
        - Thử diễn đạt câu hỏi khác cách
        - Liên hệ trực tiếp với phòng ban liên quan
        - Kiểm tra website chính thức của trường
        
        Tôi sẵn sàng hỗ trợ bạn với các vấn đề khác!
        """
        
        return {
            "reply": fallback_answer,
            "agent": "enhanced_rag", 
            "sources": [],
            "search_info": {
                "original_query": optimized_query,
                "documents_found": 0,
                "search_success": False,
                "suggestion": "Try rephrasing the question or contact relevant department"
            }
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Tạo response khi có lỗi"""
        
        return {
            "reply": "Xin lỗi, tôi gặp sự cố khi tìm kiếm thông tin. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.",
            "agent": "enhanced_rag",
            "error": error_message,
            "sources": [],
            "search_info": {
                "search_success": False,
                "error": True
            }
        }
    
    async def ingest_documents(self, documents: List[Dict]) -> Dict:
        """Ingest tài liệu mới vào knowledge base"""
        
        if not HTTPX_AVAILABLE:
            return {"success": False, "error": "httpx not available"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.policy_service_url}/ingest_policies",
                    json={"documents": documents},
                    timeout=60.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_knowledge_coverage(self, query: str) -> Dict:
        """Kiểm tra độ bao phủ kiến thức cho một query"""
        
        if not HTTPX_AVAILABLE:
            return {"has_relevant_info": False, "coverage_score": 0.0}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.policy_service_url}/check",
                    json={"text": query},
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "has_relevant_info": result.get("needs_answer", False),
                    "citations": result.get("citations", []),
                    "coverage_score": len(result.get("citations", [])) / self.max_citations
                }
                
        except Exception as e:
            logger.error(f"Error checking knowledge coverage: {e}")
            return {"has_relevant_info": False, "coverage_score": 0.0}
    
    def _rule_based_query_optimization(self, user_message: str) -> str:
        """Rule-based query optimization fallback"""
        
        # Remove common stop words
        stop_words = ["tôi", "mình", "em", "anh", "chị", "bạn", "là", "có", "được", "thể", "như", "thế", "nào"]
        
        # Extract important keywords
        important_keywords = {
            "học phí": ["học phí", "tuition", "fee", "payment"],
            "đăng ký": ["đăng ký", "registration", "enroll"],
            "lịch thi": ["lịch thi", "exam schedule", "thi cử"],
            "ký túc xá": ["ký túc xá", "dormitory", "dorm", "phòng"],
            "thư viện": ["thư viện", "library", "sách"],
            "học bổng": ["học bổng", "scholarship", "grant"],
            "chuyển ngành": ["chuyển ngành", "transfer", "đổi ngành"],
            "thời khóa biểu": ["thời khóa biểu", "schedule", "lịch học"]
        }
        
        query_lower = user_message.lower()
        
        # Find matching keywords
        for topic, keywords in important_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                # Add related terms
                return f"{user_message} {' '.join(keywords[:2])}"
        
        # Remove stop words for general queries
        words = user_message.split()
        filtered_words = [word for word in words if word.lower() not in stop_words]
        
        return " ".join(filtered_words) if filtered_words else user_message
