import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Key, BookOpen, CalendarCheck } from 'lucide-react';
import { selfService, UserProfile, CallToolRequest } from '@/services/self';

interface ActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  intent: 'reset_password' | 'renew_library' | 'book_room';
  userProfile?: UserProfile;
}

export const ActionModal = ({ isOpen, onClose, intent, userProfile }: ActionModalProps) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const { toast } = useToast();

  const actionConfig = {
    reset_password: {
      title: 'Reset Password',
      description: 'Reset your account password. You will receive instructions via email.',
      icon: Key,
      fields: [
        { key: 'email', label: 'Email Address', type: 'email', required: true },
        { key: 'reason', label: 'Reason for Reset', type: 'textarea', required: false }
      ]
    },
    renew_library: {
      title: 'Renew Library Card',
      description: 'Extend your library card validity period.',
      icon: BookOpen,
      fields: [
        { key: 'card_number', label: 'Library Card Number', type: 'text', required: false },
        { key: 'duration', label: 'Renewal Duration (months)', type: 'number', required: false },
        { key: 'notes', label: 'Additional Notes', type: 'textarea', required: false }
      ]
    },
    book_room: {
      title: 'Book Study Room',
      description: 'Reserve a study room for your academic activities.',
      icon: CalendarCheck,
      fields: [
        { key: 'room_type', label: 'Room Type', type: 'select', required: true, options: ['Individual', 'Group (4-6)', 'Group (8-10)', 'Conference Room'] },
        { key: 'date', label: 'Date', type: 'date', required: true },
        { key: 'start_time', label: 'Start Time', type: 'time', required: true },
        { key: 'end_time', label: 'End Time', type: 'time', required: true },
        { key: 'purpose', label: 'Purpose', type: 'textarea', required: true }
      ]
    }
  };

  const config = actionConfig[intent];
  const Icon = config.icon;

  // Pre-fill form with user profile data
  const getDefaultValue = (fieldKey: string) => {
    if (fieldKey === 'email' && userProfile?.student_id) {
      return `${userProfile.student_id}@university.edu`;
    }
    if (fieldKey === 'card_number' && userProfile?.student_id) {
      return userProfile.student_id;
    }
    if (fieldKey === 'duration') {
      return '12';
    }
    return formData[fieldKey] || '';
  };

  const handleInputChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validate required fields
      const missingFields = config.fields
        .filter(field => field.required && !getDefaultValue(field.key))
        .map(field => field.label);

      if (missingFields.length > 0) {
        toast({
          title: 'Validation Error',
          description: `Please fill in: ${missingFields.join(', ')}`,
          variant: 'destructive',
        });
        return;
      }

      // Prepare request data
      const requestData: CallToolRequest = {
        intent,
        parameters: {
          student_id: userProfile?.student_id,
          ...Object.fromEntries(
            config.fields.map(field => [field.key, getDefaultValue(field.key)])
          )
        }
      };

      const response = await selfService.callTool(requestData);

      if (response.success) {
        toast({
          title: 'Success',
          description: response.message,
        });
        onClose();
        setFormData({});
      } else {
        toast({
          title: 'Error',
          description: response.message,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process request. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon className="h-5 w-5" />
            {config.title}
          </DialogTitle>
          <DialogDescription>
            {config.description}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {config.fields.map((field) => (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={field.key}>
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              
              {field.type === 'textarea' ? (
                <Textarea
                  id={field.key}
                  value={getDefaultValue(field.key)}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  placeholder={`Enter ${field.label.toLowerCase()}`}
                  className="min-h-[80px]"
                />
              ) : field.type === 'select' ? (
                <select
                  id={field.key}
                  value={getDefaultValue(field.key)}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Select {field.label}</option>
                  {field.options?.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              ) : (
                <Input
                  id={field.key}
                  type={field.type}
                  value={getDefaultValue(field.key)}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  placeholder={`Enter ${field.label.toLowerCase()}`}
                />
              )}
            </div>
          ))}

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Submit Request'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
