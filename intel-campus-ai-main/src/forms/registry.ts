// Form registry for dynamic form generation based on intent
export type Intent = 'reset_password' | 'renew_library_card' | 'book_room' | 'create_glpi_ticket' | 'request_dorm_fix';

export interface FormConfig {
  schema: any; // JSON Schema for validation
  uiSchema?: any; // UI Schema for form rendering
  prefill: (profile: any, context?: any) => any; // Function to prefill form values
  toolName: string; // Corresponding tool name in action service
}

export const FORM_REGISTRY: Record<Intent, FormConfig> = {
  reset_password: {
    schema: {
      type: 'object',
      properties: {
        student_id: {
          type: 'string',
          title: 'Student ID',
          description: 'Your student ID for password reset'
        }
      },
      required: ['student_id']
    },
    uiSchema: {
      student_id: {
        'ui:widget': 'text',
        'ui:placeholder': 'Enter your student ID',
        'ui:disabled': true // Pre-filled from profile
      }
    },
    prefill: (profile, context) => ({
      student_id: profile?.student_id || context?.student_id || ''
    }),
    toolName: 'reset_password'
  },

  renew_library_card: {
    schema: {
      type: 'object',
      properties: {
        student_id: {
          type: 'string',
          title: 'Student ID',
          description: 'Your student ID'
        },
        card_number: {
          type: 'string',
          title: 'Library Card Number',
          description: 'Your library card number to renew'
        },
        duration: {
          type: 'string',
          title: 'Renewal Duration',
          enum: ['3_months', '6_months', '1_year'],
          enumNames: ['3 Months', '6 Months', '1 Year'],
          default: '6_months'
        }
      },
      required: ['student_id', 'card_number', 'duration']
    },
    uiSchema: {
      student_id: {
        'ui:disabled': true
      },
      card_number: {
        'ui:placeholder': 'Enter your library card number'
      },
      duration: {
        'ui:widget': 'select'
      }
    },
    prefill: (profile, context) => ({
      student_id: profile?.student_id || '',
      card_number: context?.card_number || '',
      duration: context?.duration || '6_months'
    }),
    toolName: 'renew_library_card'
  },

  book_room: {
    schema: {
      type: 'object',
      properties: {
        room_id: {
          type: 'string',
          title: 'Room ID',
          description: 'The room you want to book'
        },
        start_time: {
          type: 'string',
          format: 'date-time',
          title: 'Start Time',
          description: 'When you want to start using the room'
        },
        end_time: {
          type: 'string',
          format: 'date-time',
          title: 'End Time',
          description: 'When you want to finish using the room'
        },
        purpose: {
          type: 'string',
          title: 'Purpose',
          description: 'Why you need to book this room'
        }
      },
      required: ['room_id', 'start_time', 'end_time']
    },
    uiSchema: {
      room_id: {
        'ui:placeholder': 'e.g., A101, B205'
      },
      start_time: {
        'ui:widget': 'datetime'
      },
      end_time: {
        'ui:widget': 'datetime'
      },
      purpose: {
        'ui:widget': 'textarea',
        'ui:placeholder': 'Brief description of your activity'
      }
    },
    prefill: (profile, context) => ({
      room_id: context?.room_id || '',
      start_time: context?.start_time || '',
      end_time: context?.end_time || '',
      purpose: context?.purpose || ''
    }),
    toolName: 'book_room'
  },

  create_glpi_ticket: {
    schema: {
      type: 'object',
      properties: {
        title: {
          type: 'string',
          title: 'Ticket Title',
          description: 'Brief description of the issue'
        },
        description: {
          type: 'string',
          title: 'Description',
          description: 'Detailed description of the problem'
        },
        category: {
          type: 'string',
          title: 'Category',
          enum: ['technical', 'account', 'facility', 'other'],
          enumNames: ['Technical Issue', 'Account Problem', 'Facility Issue', 'Other']
        },
        priority: {
          type: 'string',
          title: 'Priority',
          enum: ['low', 'normal', 'high', 'urgent'],
          enumNames: ['Low', 'Normal', 'High', 'Urgent'],
          default: 'normal'
        }
      },
      required: ['title', 'description', 'category']
    },
    uiSchema: {
      title: {
        'ui:placeholder': 'e.g., Cannot access WiFi'
      },
      description: {
        'ui:widget': 'textarea',
        'ui:placeholder': 'Please provide as much detail as possible...'
      },
      category: {
        'ui:widget': 'select'
      },
      priority: {
        'ui:widget': 'select'
      }
    },
    prefill: (profile, context) => ({
      title: context?.title || '',
      description: context?.description || '',
      category: context?.category || 'technical',
      priority: context?.priority || 'normal'
    }),
    toolName: 'create_glpi_ticket'
  },

  request_dorm_fix: {
    schema: {
      type: 'object',
      properties: {
        room_number: {
          type: 'string',
          title: 'Room Number',
          description: 'Your dormitory room number'
        },
        issue_type: {
          type: 'string',
          title: 'Issue Type',
          enum: ['electrical', 'plumbing', 'furniture', 'cleaning', 'other'],
          enumNames: ['Electrical', 'Plumbing', 'Furniture', 'Cleaning', 'Other']
        },
        description: {
          type: 'string',
          title: 'Issue Description',
          description: 'Describe the problem in detail'
        },
        urgency: {
          type: 'string',
          title: 'Urgency Level',
          enum: ['low', 'medium', 'high', 'emergency'],
          enumNames: ['Low', 'Medium', 'High', 'Emergency'],
          default: 'medium'
        }
      },
      required: ['room_number', 'issue_type', 'description']
    },
    uiSchema: {
      room_number: {
        'ui:placeholder': 'e.g., A301, B205'
      },
      issue_type: {
        'ui:widget': 'select'
      },
      description: {
        'ui:widget': 'textarea',
        'ui:placeholder': 'Please describe the issue...'
      },
      urgency: {
        'ui:widget': 'select'
      }
    },
    prefill: (profile, context) => ({
      room_number: context?.room_number || '',
      issue_type: context?.issue_type || 'other',
      description: context?.description || '',
      urgency: context?.urgency || 'medium'
    }),
    toolName: 'request_dorm_fix'
  }
};

// Helper function to get form config by intent
export const getFormConfig = (intent: Intent): FormConfig | null => {
  return FORM_REGISTRY[intent] || null;
};

// Helper function to validate if intent exists
export const isValidIntent = (intent: string): intent is Intent => {
  return intent in FORM_REGISTRY;
};

// Get all available intents
export const getAvailableIntents = (): Intent[] => {
  return Object.keys(FORM_REGISTRY) as Intent[];
};
