# Lead-Agent System Implementation Guide

## Tổng quan Kiến trúc Mới

Hệ thống đã được nâng cấp từ simple routing sang **Lead-Agent Orchestration** với khả năng:

### 1. **Lead Agent (Orchestrator)**
- **Phân tích độ phức tạp** yêu cầu và quyết định cách tiếp cận
- **Lập kế hoạch** (workflow planning) cho tasks phức tạp  
- **Điều phối** nhiều subagents theo workflow
- **Tổng hợp** kết quả từ các agents thành response hoàn chỉnh

### 2. **Specialized Agents**
- **Action Executor Agent**: Thực hiện tools/actions cụ thể
- **Enhanced RAG Agent**: Tìm kiếm và trả lời dựa trên knowledge base
- **Critic Agent**: Đánh giá chất lượng và phản biện
- **Technical/FAQ/Greeting Agents**: Xử lý chuyên môn theo lĩnh vực

### 3. **Tool Integration** 
- **Standardized tool-calling** thông qua Action service
- **Parameter extraction và validation**
- **Error handling và fallback mechanisms**

## Quy trình Hoạt động

### Simple Request Flow:
```
User Request → Lead Agent → Complexity Analysis → Simple Routing → Specialized Agent → Response
```

### Complex Request Flow:
```
User Request → Lead Agent → Workflow Planning → Multi-step Execution:
    Step 1: FAQ Agent (tìm policy)
    Step 2: Action Executor (thực hiện tool)  
    Step 3: Critic Agent (đánh giá)
→ Result Synthesis → Final Response
```

## Implementation Details

### 1. Lead Agent (`lead_agent.py`)
```python
class LeadAgent:
    - analyze_complexity(): Phân tích độ phức tạp yêu cầu
    - create_workflow_plan(): Lập kế hoạch chi tiết
    - execute_workflow(): Thực hiện workflow step-by-step
    - synthesize_results(): Tổng hợp kết quả cuối cùng
```

### 2. Action Executor (`action_executor.py`)
```python
class ActionExecutorAgent:
    - analyze_tool_request(): Xác định tool cần dùng
    - extract_tool_parameters(): Trích xuất params từ user input
    - validate_parameters(): Kiểm tra tính hợp lệ
    - execute_tool(): Gọi Action service
```

### 3. Enhanced RAG (`enhanced_rag.py`)
```python
class EnhancedRAGAgent:
    - optimize_search_query(): Tối ưu query tìm kiếm
    - search_documents(): Tìm kiếm từ Policy service
    - rerank_and_filter(): Sắp xếp theo độ liên quan
    - generate_answer(): Tạo answer từ documents
```

### 4. Critic Agent (`critic.py`)
```python
class CriticAgent:
    - evaluate_response(): Đánh giá theo 6 tiêu chí
    - generate_improvement_suggestions(): Đề xuất cải thiện
    - evaluate_workflow_result(): Đánh giá toàn bộ workflow
```

## Tool-calling Integration

### Available Tools:
1. **reset_password**: Đặt lại mật khẩu sinh viên
2. **renew_library_card**: Gia hạn thẻ thư viện
3. **book_room**: Đặt phòng học/họp
4. **create_glpi_ticket**: Tạo ticket hỗ trợ
5. **request_dorm_fix**: Yêu cầu sửa chữa ký túc xá

### Tool Call Flow:
```
User Request → Lead Agent → Action Executor Agent → Parameter Extraction → 
Validation → Action Service API Call → Result Processing → User Response
```

## Configuration

### Environment Variables:
```bash
# Lead-Agent Settings
LEAD_AGENT_MAX_WORKFLOWS=100
LEAD_AGENT_COMPLEXITY_THRESHOLD=0.7
LEAD_AGENT_ENABLE_CRITIC=true

# Performance
MAX_CONCURRENT_WORKFLOWS=10
AGENT_RESPONSE_TIMEOUT=60
```

### Docker Compose Integration:
- All agents run within Gateway service
- Async communication với Action/Policy services
- Redis cho workflow state management

## API Endpoints

### New Endpoints:
```
GET /tools - Danh sách tools có sẵn
POST /call_tool - Thực hiện tool call
GET /workflows/{id} - Trạng thái workflow
POST /evaluate - Đánh giá response quality
```

### Enhanced Endpoints:
```
POST /ask - Enhanced với Lead-Agent orchestration
GET /agents - Bao gồm new agents  
GET /health - Monitor agent health
```

## Memory và State Management

### Session Memory:
- Lưu context giữa các interactions
- Student info và preferences
- Previous actions và results

### Workflow State:
- Active workflows tracking
- Step completion status  
- Inter-step data passing
- Error và retry logic

## Error Handling

### Fallback Mechanisms:
1. **Agent unavailable** → Fallback to simpler agent
2. **Tool execution failed** → Alternative approaches
3. **LLM parsing error** → Default responses
4. **Service unavailable** → Graceful degradation

### Logging và Monitoring:
- Structured logging cho all agent interactions
- Performance metrics
- Error tracking và alerting

## Extensibility

### Adding New Agents:
1. Inherit from `BaseAgent`
2. Implement `process()` method
3. Add to `EnhancedAgentManager`
4. Update Lead Agent planning logic

### Adding New Tools:
1. Update Action service với new tool
2. Add schema to `TOOL_SCHEMAS`
3. Update Action Executor tool mapping
4. Test parameter extraction logic

## Testing Strategy

### Unit Tests:
- Individual agent logic
- Tool parameter extraction
- Workflow planning accuracy

### Integration Tests:
- End-to-end workflows
- Service communication
- Error scenarios

### Performance Tests:
- Concurrent workflow handling
- Response time under load
- Memory usage optimization

## Deployment Considerations

### Resource Requirements:
- Increased memory for workflow state
- CPU overhead cho planning logic
- Network bandwidth cho inter-service calls

### Monitoring:
- Agent response times
- Workflow success rates
- Tool execution statistics
- Error patterns analysis

## Next Steps

1. **Testing**: Comprehensive testing của new system
2. **Optimization**: Performance tuning based on usage
3. **Documentation**: User guides cho complex features
4. **Training**: Staff training on new capabilities
5. **Gradual Rollout**: Phased deployment strategy
