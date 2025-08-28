import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { SmartForm } from '@/components/SmartForm';
import { getAvailableIntents, type Intent } from '@/forms/registry';

const SmartFormDemo: React.FC = () => {
  const [selectedIntent, setSelectedIntent] = useState<Intent | null>(null);
  const [context, setContext] = useState<any>({});
  const [results, setResults] = useState<any[]>([]);

  const availableIntents = getAvailableIntents();

  const handleFormDone = (result: any) => {
    setResults(prev => [...prev, {
      intent: selectedIntent,
      timestamp: new Date().toISOString(),
      result
    }]);
    setSelectedIntent(null);
  };

  const handleFormCancel = () => {
    setSelectedIntent(null);
  };

  const presetContexts = {
    reset_password: {},
    renew_library_card: {
      card_number: 'LIB123456',
      duration: '6_months'
    },
    book_room: {
      room_id: 'A101',
      purpose: 'Study group meeting'
    },
    create_glpi_ticket: {
      category: 'technical',
      title: 'WiFi connection issue'
    },
    request_dorm_fix: {
      room_number: 'D305',
      issue_type: 'electrical',
      urgency: 'high'
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Smart Form Demo</h1>
        <p className="text-muted-foreground">
          Test dynamic form generation based on intent and JSON schema
        </p>
      </div>

      {!selectedIntent ? (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Intent Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Intent</CardTitle>
              <CardDescription>
                Choose an action to generate its corresponding form
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                {availableIntents.map((intent) => (
                  <Button
                    key={intent}
                    variant="outline"
                    className="justify-start"
                    onClick={() => {
                      setSelectedIntent(intent);
                      setContext(presetContexts[intent] || {});
                    }}
                  >
                    <Badge variant="secondary" className="mr-2">
                      {intent.replace('_', ' ').toUpperCase()}
                    </Badge>
                    {intent === 'reset_password' && 'Reset Password'}
                    {intent === 'renew_library_card' && 'Renew Library Card'}
                    {intent === 'book_room' && 'Book Study Room'}
                    {intent === 'create_glpi_ticket' && 'Create Support Ticket'}
                    {intent === 'request_dorm_fix' && 'Request Dorm Repair'}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Results History */}
          <Card>
            <CardHeader>
              <CardTitle>Submission History</CardTitle>
              <CardDescription>
                Recent form submissions and their results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {results.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  No submissions yet. Try filling out a form!
                </p>
              ) : (
                <div className="space-y-3">
                  {results.slice().reverse().map((result, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">
                          {result.intent?.replace('_', ' ').toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(result.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm">
                        Status: 
                        <Badge 
                          variant={result.result.status === 'success' ? 'default' : 'destructive'}
                          className="ml-2"
                        >
                          {result.result.status}
                        </Badge>
                      </p>
                      {result.result.message && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {result.result.message}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Form Header */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">
                    {selectedIntent.replace('_', ' ').toUpperCase()} Form
                  </h2>
                  <p className="text-muted-foreground">
                    Dynamic form generated from JSON schema
                  </p>
                </div>
                <Badge variant="outline">
                  {Object.keys(context).length > 0 ? 'With Context' : 'No Context'}
                </Badge>
              </div>
              
              {Object.keys(context).length > 0 && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Context Data:</p>
                  <pre className="text-xs overflow-auto">
                    {JSON.stringify(context, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Smart Form */}
          <SmartForm
            intent={selectedIntent}
            context={context}
            onDone={handleFormDone}
            onCancel={handleFormCancel}
          />
        </div>
      )}

      {/* Testing Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-800">Testing Instructions</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-700 space-y-2">
          <p><strong>Reset Password:</strong> Should prefill student_id, only need to click "Confirm"</p>
          <p><strong>Book Room:</strong> If context has room_id, it prefills; missing time fields will be highlighted</p>
          <p><strong>Library Card:</strong> Test with card number pre-filled from context</p>
          <p><strong>Form Validation:</strong> Try submitting with missing required fields to see validation</p>
          <p><strong>Preview Mode:</strong> Click "Preview" to see the payload that will be sent</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default SmartFormDemo;
