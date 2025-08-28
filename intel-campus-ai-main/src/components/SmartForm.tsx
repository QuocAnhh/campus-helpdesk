import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, Eye, EyeOff, Send, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getFormConfig, type Intent } from '@/forms/registry';
import { getMe, callTool } from '@/services/self';

// Helper to convert JSON Schema to Zod schema
const jsonSchemaToZod = (schema: any): z.ZodSchema => {
  if (schema.type === 'object') {
    const shape: Record<string, z.ZodSchema> = {};
    
    for (const [key, prop] of Object.entries(schema.properties || {})) {
      const property = prop as any;
      let zodSchema: z.ZodSchema;

      if (property.type === 'string') {
        if (property.enum) {
          zodSchema = z.enum(property.enum);
        } else if (property.format === 'date-time') {
          zodSchema = z.string().datetime();
        } else {
          zodSchema = z.string();
        }
      } else if (property.type === 'number') {
        zodSchema = z.number();
      } else if (property.type === 'boolean') {
        zodSchema = z.boolean();
      } else {
        zodSchema = z.string();
      }

      // Make field optional if not required
      if (!schema.required?.includes(key)) {
        zodSchema = zodSchema.optional();
      }

      shape[key] = zodSchema;
    }

    return z.object(shape);
  }
  
  return z.object({});
};

interface SmartFormProps {
  intent: Intent;
  context?: any;
  onDone?: (result: any) => void;
  onCancel?: () => void;
}

interface UserProfile {
  student_id: string;
  name: string;
  major: string;
}

export const SmartForm: React.FC<SmartFormProps> = ({
  intent,
  context,
  onDone,
  onCancel
}) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const { toast } = useToast();

  const formConfig = getFormConfig(intent);
  
  const zodSchema = formConfig ? jsonSchemaToZod(formConfig.schema) : z.object({});
  
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
    reset
  } = useForm({
    resolver: zodResolver(zodSchema),
    mode: 'onChange'
  });

  const watchedValues = watch();

  // Load user profile and prefill form
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const userProfile = await getMe();
        setProfile(userProfile);
        
        if (formConfig) {
          const initialValues = formConfig.prefill(userProfile, context);
          
          // Set form values
          Object.entries(initialValues).forEach(([key, value]) => {
            setValue(key, value);
          });
        }
      } catch (error) {
        console.error('Failed to load profile:', error);
        // Use mock data if API fails
        const mockProfile = { student_id: 'student123', name: 'Unknown', major: 'Unknown' };
        setProfile(mockProfile);
        
        if (formConfig) {
          const initialValues = formConfig.prefill(mockProfile, context);
          Object.entries(initialValues).forEach(([key, value]) => {
            setValue(key, value);
          });
        }
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, [intent, context, formConfig, setValue]);

  const onSubmit = async (data: any) => {
    if (!formConfig) return;

    setSubmitting(true);
    try {
      const response = await callTool(formConfig.toolName, data);
      
      toast({
        title: 'Success',
        description: response.message || 'Action completed successfully',
      });

      onDone?.(response);
    } catch (error: any) {
      console.error('Tool call failed:', error);
      
      toast({
        title: 'Error',
        description: error.response?.data?.detail?.message || error.message || 'Action failed',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (fieldName: string, fieldSchema: any) => {
    const error = errors[fieldName];
    const value = watchedValues[fieldName] || '';
    const isRequired = formConfig?.schema.required?.includes(fieldName);
    const uiConfig = formConfig?.uiSchema?.[fieldName] || {};

    const fieldProps = {
      ...register(fieldName),
      placeholder: uiConfig['ui:placeholder'] || fieldSchema.description,
      disabled: uiConfig['ui:disabled'] || submitting
    };

    return (
      <div key={fieldName} className="space-y-2">
        <Label htmlFor={fieldName} className="flex items-center gap-2">
          {fieldSchema.title || fieldName}
          {isRequired && <Badge variant="destructive" className="text-xs">Required</Badge>}
        </Label>
        
        {fieldSchema.enum ? (
          <Select value={value} onValueChange={(val) => setValue(fieldName, val)}>
            <SelectTrigger>
              <SelectValue placeholder={`Select ${fieldSchema.title || fieldName}`} />
            </SelectTrigger>
            <SelectContent>
              {fieldSchema.enum.map((option: string, index: number) => (
                <SelectItem key={option} value={option}>
                  {fieldSchema.enumNames?.[index] || option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : uiConfig['ui:widget'] === 'textarea' ? (
          <Textarea
            id={fieldName}
            {...fieldProps}
            className={error ? 'border-red-500' : ''}
          />
        ) : fieldSchema.format === 'date-time' ? (
          <Input
            id={fieldName}
            type="datetime-local"
            {...fieldProps}
            className={error ? 'border-red-500' : ''}
          />
        ) : (
          <Input
            id={fieldName}
            type="text"
            {...fieldProps}
            className={error ? 'border-red-500' : ''}
          />
        )}

        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {(error as any)?.message || 'This field is required'}
            </AlertDescription>
          </Alert>
        )}

        {fieldSchema.description && !uiConfig['ui:placeholder'] && (
          <p className="text-sm text-muted-foreground">{fieldSchema.description}</p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Loading form...
        </CardContent>
      </Card>
    );
  }

  if (!formConfig) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Form configuration not found for intent: {intent}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const requiredFields = formConfig.schema.required || [];
  const missingFields = requiredFields.filter(field => !watchedValues[field]);

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {formConfig.schema.title || `${intent.replace('_', ' ').toUpperCase()}`}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {showPreview ? 'Hide' : 'Preview'}
          </Button>
        </CardTitle>
        {formConfig.schema.description && (
          <CardDescription>{formConfig.schema.description}</CardDescription>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Show missing required fields warning */}
        {missingFields.length > 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Please fill in the required fields: {missingFields.join(', ')}
            </AlertDescription>
          </Alert>
        )}

        {/* Preview payload */}
        {showPreview && (
          <Alert>
            <AlertDescription>
              <strong>Payload Preview:</strong>
              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto">
                {JSON.stringify({
                  tool_name: formConfig.toolName,
                  tool_args: watchedValues
                }, null, 2)}
              </pre>
            </AlertDescription>
          </Alert>
        )}

        {/* Form fields */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {Object.entries(formConfig.schema.properties || {}).map(([fieldName, fieldSchema]) =>
            renderField(fieldName, fieldSchema as any)
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={submitting}
              >
                Cancel
              </Button>
            )}
            
            <Button
              type="submit"
              disabled={!isValid || submitting || missingFields.length > 0}
              className="min-w-[120px]"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Confirm
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
