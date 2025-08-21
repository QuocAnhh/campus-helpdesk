"""
Provider-agnostic interface for Large Language Models.
"""
import os
import json
from typing import List, Dict, Optional

# --- Provider-specific imports ---
from openai import OpenAI
import google.generativeai as genai

# --- OpenAI Configuration ---
openai_client = None

# --- Gemini Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo") # Default model

def chat(messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
    """
    Sends a chat request to the configured LLM provider.
    """
    provider = os.getenv("LLM_PROVIDER", "stub").lower()

    if provider == "openai":
        model = LLM_MODEL if LLM_MODEL != "gpt-3.5-turbo" else "gpt-4o-mini"
        return _openai_chat(messages, model, tools)
    elif provider == "gemini":
        model = LLM_MODEL if LLM_MODEL != "gpt-3.5-turbo" else "gemini-1.5-flash"
        return _gemini_chat(messages, model, tools)
    elif provider == "vllm":
        raise NotImplementedError("vLLM provider not yet implemented.")
    elif provider == "ollama":
        raise NotImplementedError("Ollama provider not yet implemented.")
    else:
        return stub_chat(messages, tools)

def _openai_chat(messages: List[Dict], model: str, tools: Optional[List[Dict]] = None) -> Dict:
    """
    Handles the chat completion call to OpenAI.
    """
    global openai_client
    if openai_client is None:
        openai_client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            temperature=0.7,
        )
        message = response.choices[0].message
        if message.tool_calls:
            return {"tool_calls": [tc.model_dump() for tc in message.tool_calls]}
        return {"content": message.content}
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return stub_chat(messages, tools)

def _gemini_chat(messages: List[Dict], model: str, tools: Optional[List[Dict]] = None) -> Dict:
    """
    Handles the chat completion call to Google Gemini.
    """
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found. Falling back to stub.")
        return stub_chat(messages, tools)
    
    try:
        # Convert messages to Gemini's format (history + current message)
        # Note: Gemini's message format is slightly different. Roles are 'user' and 'model'.
        gemini_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                # Gemini doesn't have a 'system' role in the same way. We prepend it to the first user message.
                # This is a common workaround.
                if gemini_messages:
                     gemini_messages[0]['parts'].insert(0, msg["content"])
                else: # if the system prompt is the very first message
                    gemini_messages.append({'role': 'user', 'parts': [msg["content"]]})
            elif role == "user":
                if gemini_messages and gemini_messages[-1]['role'] == 'user':
                     gemini_messages[-1]['parts'].append(msg["content"])
                else:
                    gemini_messages.append({'role': 'user', 'parts': [msg["content"]]})
            elif role == "assistant":
                gemini_messages.append({'role': 'model', 'parts': [msg["content"]]})
        
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(
            gemini_messages,
            tools=tools
        )

        # Extract content from the response
        # This part might need adjustment based on the exact response structure for your model version
        if response.candidates and response.candidates[0].content.parts:
            # For now, we assume the content is text and return it.
            # If the model returns a tool call, you would handle it here.
            # Gemini tool call handling is different from OpenAI's.
            
            # Simple text extraction
            first_part = response.candidates[0].content.parts[0]
            if hasattr(first_part, 'text'):
                return {"content": first_part.text}
            # TODO: Add proper handling for Gemini tool calls if needed
            
        return {"content": "Sorry, I could not process the response from Gemini."}

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return stub_chat(messages, tools)

def stub_chat(messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
    """
    A simple rule-based stub for the chat function that works with multi-agent system.
    """
    print("Using stub LLM chat.")
    last_message = messages[-1].get("content", "").lower()
    
    # Detect if this is a router agent call
    system_message = messages[0].get("content", "")
    if "router agent" in system_message.lower():
        # Router logic
        if "chào" in last_message or "hello" in last_message or "alo" in last_message:
            return {"content": json.dumps({
                "target_agent": "greeting",
                "reason": "Người dùng đang chào hỏi",
                "confidence": 0.9,
                "extracted_info": {
                    "key_entities": ["chào hỏi"],
                    "intent_keywords": ["chào", "hello", "alo"],
                    "urgency": "low"
                }
            })}
        elif "mật khẩu" in last_message or "password" in last_message:
            return {"content": json.dumps({
                "target_agent": "technical",
                "reason": "Yêu cầu hỗ trợ kỹ thuật về mật khẩu",
                "confidence": 0.95,
                "extracted_info": {
                    "key_entities": ["mật khẩu"],
                    "intent_keywords": ["đặt lại", "reset", "quên"],
                    "urgency": "medium"
                }
            })}
        else:
            return {"content": json.dumps({
                "target_agent": "faq",
                "reason": "Câu hỏi thông tin chung",
                "confidence": 0.7,
                "extracted_info": {
                    "key_entities": [],
                    "intent_keywords": [],
                    "urgency": "low"
                }
            })}
    
    # Agent responses
    elif "greeting agent" in system_message.lower():
        return {"content": "Chào bạn! Mình là trợ lý Campus Helpdesk. Hôm nay mình có thể giúp gì cho bạn?"}
    elif "technical" in system_message.lower():
        return {"content": "Mình sẽ giúp bạn với vấn đề kỹ thuật. Bạn có thể cho mình biết chi tiết hơn về vấn đề bạn đang gặp phải không?"}
    elif "faq" in system_message.lower():
        return {"content": "Mình sẽ tìm kiếm thông tin để trả lời câu hỏi của bạn. Bạn có thể đợi một chút nhé."}
    else:
        # Default response
        return {"content": "Xin lỗi, tôi cần thêm thông tin để có thể hỗ trợ bạn tốt hơn."} 