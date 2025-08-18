"""
This module defines the JSON schema for the tools that can be called by the agent.
"""

TOOL_SCHEMAS = {
    "reset_password": {
        "type": "object",
        "properties": {
            "student_id": {"type": "string"},
        },
        "required": ["student_id"],
    },
    "create_glpi_ticket": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "category": {"type": "string"},
        },
        "required": ["title", "description", "category"],
    },
    "request_dorm_fix": {
        "type": "object",
        "properties": {
            "room_number": {"type": "string"},
            "issue_description": {"type": "string"},
        },
        "required": ["room_number", "issue_description"],
    },
    "book_room": {
        "type": "object",
        "properties": {
            "room_id": {"type": "string"},
            "start_time": {"type": "string", "format": "date-time"},
            "end_time": {"type": "string", "format": "date-time"},
        },
        "required": ["room_id", "start_time", "end_time"],
    },
} 