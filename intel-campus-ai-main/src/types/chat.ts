export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  agentInfo?: {
    name: string;
    type: string;
  };
}

export interface ChatRequest {
  channel: string;
  text: string;
  student_id: string;
  session_id: string;
}

export interface ChatResponse {
  answer: {
    reply: string;
  };
  agent_info: {
    name: string;
    type: string;
  };
}

export interface HealthStatus {
  status: string;
  available_agents: string[];
  total_agents: number;
}

export interface Agent {
  name: string;
  type: string;
  status: string;
}