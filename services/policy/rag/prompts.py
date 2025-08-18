"""
This module contains the prompts for the RAG model.
"""

# TODO: Add system and user prompts for citations-first answering in Vietnamese.

SYSTEM_PROMPT = """
Bạn là một trợ lý ảo của trường đại học.
Nhiệm vụ của bạn là trả lời các câu hỏi về chính sách của trường.
"""

USER_PROMPT_TEMPLATE = """
Dựa vào các thông tin sau đây:
{context}

Hãy trả lời câu hỏi:
{question}
""" 