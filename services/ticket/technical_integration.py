import os
import httpx
from typing import Optional, Dict, Any
import schemas
import models

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")

class TechnicalAgentIntegration:
    """Integration with the technical agent for ticket analysis"""
    
    def __init__(self):
        self.gateway_url = GATEWAY_URL
    
    async def analyze_ticket(self, ticket: models.Ticket, user_token: str) -> Optional[Dict[str, Any]]:
        """Send ticket to technical agent for analysis"""
        try:
            # Prepare the message for technical agent
            analysis_request = {
                "channel": "ticket",
                "text": f"Technical Support Request:\n\nSubject: {ticket.subject}\n\nDescription: {ticket.content}\n\nCategory: {ticket.category}\nPriority: {ticket.priority}\n\nPlease analyze this technical issue and provide recommendations.",
                "student_id": str(ticket.user_id),
                "session_id": f"ticket_{ticket.id}",
                "ticket_id": ticket.id
            }
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {user_token}"}
                response = await client.post(
                    f"{self.gateway_url}/ask",
                    json=analysis_request,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "analysis": result.get("answer", {}).get("reply", ""),
                        "agent_info": result.get("answer", {}).get("agent_info", {}),
                        "sources": result.get("answer", {}).get("agent_info", {}).get("sources", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Technical agent returned status {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error communicating with technical agent: {str(e)}"
            }
    
    async def suggest_solution(self, ticket: models.Ticket, user_token: str) -> Optional[Dict[str, Any]]:
        """Get solution suggestions from technical agent"""
        try:
            # Create a more specific request for solutions
            solution_request = {
                "channel": "ticket_solution",
                "text": f"Please provide step-by-step solution for this technical issue:\n\nProblem: {ticket.subject}\n\nDetails: {ticket.content}\n\nProvide clear, actionable steps to resolve this issue.",
                "student_id": str(ticket.user_id),
                "session_id": f"ticket_solution_{ticket.id}",
                "ticket_id": ticket.id
            }
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {user_token}"}
                response = await client.post(
                    f"{self.gateway_url}/ask",
                    json=solution_request,
                    headers=headers,
                    timeout=30.0,
                )                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "solution": result.get("answer", {}).get("reply", ""),
                        "agent_info": result.get("answer", {}).get("agent_info", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Technical agent returned status {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting solution from technical agent: {str(e)}"
            }
    
    def determine_category(self, ticket_content: str) -> models.TicketCategory:
        """Determine ticket category based on content (simple keyword matching)"""
        content_lower = ticket_content.lower()
        
        # Technical keywords
        technical_keywords = [
            "login", "password", "error", "bug", "crash", "slow", "network",
            "internet", "wifi", "computer", "laptop", "software", "app",
            "system", "technical", "code", "programming", "database"
        ]
        
        # Account keywords
        account_keywords = [
            "account", "profile", "registration", "access", "permission",
            "username", "email", "verification"
        ]
        
        # Academic keywords
        academic_keywords = [
            "grade", "course", "class", "professor", "assignment", "exam",
            "transcript", "enrollment", "credit", "academic"
        ]
        
        # Facility keywords
        facility_keywords = [
            "room", "building", "library", "lab", "equipment", "maintenance",
            "facility", "classroom", "dormitory", "cafeteria"
        ]
        
        # Count keyword matches
        if any(keyword in content_lower for keyword in technical_keywords):
            return models.TicketCategory.technical
        elif any(keyword in content_lower for keyword in account_keywords):
            return models.TicketCategory.account
        elif any(keyword in content_lower for keyword in academic_keywords):
            return models.TicketCategory.academic
        elif any(keyword in content_lower for keyword in facility_keywords):
            return models.TicketCategory.facility
        else:
            return models.TicketCategory.general
    
    def determine_priority(self, ticket_content: str, ticket_subject: str) -> models.TicketPriority:
        """Determine ticket priority based on content and subject"""
        combined_text = f"{ticket_subject} {ticket_content}".lower()
        
        # Urgent keywords
        urgent_keywords = [
            "urgent", "emergency", "critical", "can't access", "completely broken",
            "system down", "can't login", "deadline", "exam tomorrow"
        ]
        
        # High priority keywords
        high_keywords = [
            "important", "asap", "soon", "broken", "not working", "error",
            "problem", "issue", "help needed"
        ]
        
        # Low priority keywords
        low_keywords = [
            "question", "how to", "tutorial", "guide", "information",
            "when convenient", "no rush"
        ]
        
        if any(keyword in combined_text for keyword in urgent_keywords):
            return models.TicketPriority.urgent
        elif any(keyword in combined_text for keyword in high_keywords):
            return models.TicketPriority.high
        elif any(keyword in combined_text for keyword in low_keywords):
            return models.TicketPriority.low
        else:
            return models.TicketPriority.normal

# Global instance
technical_agent = TechnicalAgentIntegration() 