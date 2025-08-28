import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useAuth } from '@/context/AuthContext';
import { ticketAPI } from '@/services/api';
import { Plus, MessageSquare, Clock, CheckCircle, AlertCircle, User } from 'lucide-react';

interface Ticket {
  id: number;
  subject: string;
  content: string;  // Make sure this exists
  category: string;
  priority: string;
  status: string;
  user_name: string;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  resolution?: string;
}

const TicketsPage = () => {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  
  // Form states
  const [newTicket, setNewTicket] = useState({
    subject: '',
    content: '',
    category: 'general',
    priority: 'normal'
  });

  useEffect(() => {
    loadMyTickets();
  }, []);

  const loadMyTickets = async () => {
    try {
      setLoading(true);
      const data = await ticketAPI.getMyTickets();
      console.log('Loaded tickets:', data);
      // Log each ticket's content
      data.forEach((ticket: any, index: number) => {
        console.log(`Ticket ${index + 1} (ID: ${ticket.id}):`, {
          subject: ticket.subject,
          content: ticket.content,
          contentLength: ticket.content ? ticket.content.length : 0,
          hasContent: !!ticket.content
        });
      });
      setTickets(data);
    } catch (error) {
      console.error('Error loading tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Creating ticket with form data:', newTicket);
    
    // Validate required fields
    if (!newTicket.subject || newTicket.subject.length < 5) {
      alert('Subject must be at least 5 characters long');
      return;
    }
    
    if (!newTicket.content || newTicket.content.length < 10) {
      alert('Content must be at least 10 characters long');
      return;
    }
    
    try {
      const result = await ticketAPI.createTicket(newTicket);
      console.log('Ticket created successfully:', result);
      setNewTicket({ subject: '', content: '', category: 'general', priority: 'normal' });
      setShowCreateDialog(false);
      loadMyTickets();
    } catch (error) {
      console.error('Error creating ticket:', error);
      alert('Failed to create ticket. Please check the form data and try again.');
    }
  };

  const handleRequestAnalysis = async (ticketId: number) => {
    try {
      const result = await ticketAPI.requestTechnicalAnalysis(ticketId);
      alert(`Technical Analysis Result:\n\n${result.analysis}`);
    } catch (error) {
      console.error('Error requesting analysis:', error);
      alert('Failed to get technical analysis');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      open: { color: 'bg-blue-500', label: 'Open' },
      in_progress: { color: 'bg-yellow-500', label: 'In Progress' },
      resolved: { color: 'bg-green-500', label: 'Resolved' },
      closed: { color: 'bg-gray-500', label: 'Closed' }
    };
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.open;
    return <Badge className={`${config.color} text-white`}>{config.label}</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    const priorityConfig = {
      low: { color: 'bg-gray-400', label: 'Low' },
      normal: { color: 'bg-blue-400', label: 'Normal' },
      high: { color: 'bg-orange-400', label: 'High' },
      urgent: { color: 'bg-red-500', label: 'Urgent' }
    };
    const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.normal;
    return <Badge className={`${config.color} text-white`}>{config.label}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading your tickets...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-background px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">My Support Tickets</h1>
            <p className="text-muted-foreground">
              Track and manage your support requests
            </p>
          </div>
          
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Support Ticket</DialogTitle>
                <DialogDescription>
                  Describe your issue and we'll help you resolve it.
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleCreateTicket} className="space-y-4">
                <div>
                  <Label htmlFor="subject">Subject *</Label>
                  <Input
                    id="subject"
                    value={newTicket.subject}
                    onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                    placeholder="Brief description of your issue"
                    required
                  />
                </div>
                
                <div>
                  <Label htmlFor="content">Description *</Label>
                  <Textarea
                    id="content"
                    value={newTicket.content}
                    onChange={(e) => setNewTicket({ ...newTicket, content: e.target.value })}
                    placeholder="Detailed description of your issue..."
                    rows={4}
                    required
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="category">Category</Label>
                    <Select value={newTicket.category} onValueChange={(value) => setNewTicket({ ...newTicket, category: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">General</SelectItem>
                        <SelectItem value="technical">Technical</SelectItem>
                        <SelectItem value="account">Account</SelectItem>
                        <SelectItem value="academic">Academic</SelectItem>
                        <SelectItem value="facility">Facility</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="priority">Priority</Label>
                    <Select value={newTicket.priority} onValueChange={(value) => setNewTicket({ ...newTicket, priority: value })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Create Ticket</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto p-6">
        {tickets.length === 0 ? (
          <Card>
            <CardContent className="text-center py-20">
              <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No tickets yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first support ticket to get help with any issues.
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create First Ticket
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {tickets.map((ticket) => (
              <Card key={ticket.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{ticket.subject}</CardTitle>
                      <CardDescription className="mt-1">
                        Ticket #{ticket.id} • Created {new Date(ticket.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(ticket.status)}
                      {getPriorityBadge(ticket.priority)}
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-muted-foreground">
                      {ticket.content ? (
                        <div>
                          <p style={{ 
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}>
                            {ticket.content}
                          </p>
                          <small className="text-xs text-gray-500">
                            Content length: {ticket.content.length} chars
                          </small>
                        </div>
                      ) : (
                        <p className="italic text-gray-400">No description provided</p>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span className="flex items-center">
                          <AlertCircle className="h-4 w-4 mr-1" />
                          {ticket.category}
                        </span>
                        {ticket.assigned_to && (
                          <span className="flex items-center">
                            <User className="h-4 w-4 mr-1" />
                            Assigned to {ticket.assigned_to}
                          </span>
                        )}
                        <span className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          Updated {new Date(ticket.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                      
                      <div className="flex space-x-2">
                        {ticket.category === 'technical' && ticket.status === 'open' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRequestAnalysis(ticket.id)}
                          >
                            Get AI Analysis
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedTicket(ticket)}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                    
                    {ticket.resolution && (
                      <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
                        <div className="flex items-center mb-2">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                          <span className="font-medium text-green-800">Resolution</span>
                        </div>
                        <p className="text-green-700 text-sm">{ticket.resolution}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Ticket Detail Dialog */}
      {selectedTicket && (
        <Dialog open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedTicket.subject}</DialogTitle>
              <DialogDescription>
                Ticket #{selectedTicket.id} • Created {new Date(selectedTicket.created_at).toLocaleDateString()}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                {getStatusBadge(selectedTicket.status)}
                {getPriorityBadge(selectedTicket.priority)}
                <Badge variant="outline">{selectedTicket.category}</Badge>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Description</Label>
                {selectedTicket.content ? (
                  <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
                    {selectedTicket.content}
                  </p>
                ) : (
                  <p className="mt-1 text-sm text-gray-400 italic">No description provided</p>
                )}
              </div>
              
              {selectedTicket.assigned_to && (
                <div>
                  <Label className="text-sm font-medium">Assigned To</Label>
                  <p className="mt-1 text-sm text-muted-foreground">{selectedTicket.assigned_to}</p>
                </div>
              )}
              
              {selectedTicket.resolution && (
                <div>
                  <Label className="text-sm font-medium">Resolution</Label>
                  <div className="mt-1 p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-700">{selectedTicket.resolution}</p>
                  </div>
                </div>
              )}
              
              <div className="flex justify-end space-x-2 pt-4">
                {selectedTicket.category === 'technical' && selectedTicket.status === 'open' && (
                  <Button
                    variant="outline"
                    onClick={() => handleRequestAnalysis(selectedTicket.id)}
                  >
                    Request Technical Analysis
                  </Button>
                )}
                <Button variant="outline" onClick={() => setSelectedTicket(null)}>
                  Close
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default TicketsPage; 