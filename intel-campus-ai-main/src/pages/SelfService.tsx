import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { Loader2, User, Ticket, Settings, Key, BookOpen, CalendarCheck, RefreshCw } from 'lucide-react';
import { selfService, UserProfile, TicketSummary } from '@/services/self';
import { SmartForm } from '@/components/SmartForm';
import { UserLayout } from '@/components/layout/UserLayout';
import { type Intent } from '@/forms/registry';

export const SelfService = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [filteredTickets, setFilteredTickets] = useState<TicketSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [smartFormModal, setSmartFormModal] = useState<{
    isOpen: boolean;
    intent: Intent | null;
    context?: any;
  }>({ isOpen: false, intent: null });
  
  const { toast } = useToast();

  const loadProfile = async () => {
    try {
      const profileData = await selfService.getMe();
      setProfile(profileData);
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      toast({
        title: 'Profile Error',
        description: error.message || 'Failed to load profile',
        variant: 'destructive',
      });
      // Set mock data for development
      setProfile({
        student_id: 'student123',
        name: 'Unknown',
        major: 'Unknown'
      });
    }
  };

  const loadTickets = async () => {
    setTicketsLoading(true);
    try {
      const ticketsData = await selfService.getMyTickets();
      setTickets(ticketsData);
      setFilteredTickets(ticketsData);
    } catch (error: any) {
      console.error('Failed to load tickets:', error);
      toast({
        title: 'Tickets Error',
        description: error.message || 'Failed to load tickets',
        variant: 'destructive',
      });
      // Set mock data for development
      const mockTickets: TicketSummary[] = [
        {
          id: 1,
          subject: 'Password Reset Request',
          category: 'account',
          priority: 'normal',
          status: 'open',
          created_at: '2025-08-27T10:00:00Z'
        },
        {
          id: 2,
          subject: 'Library Card Issue',
          category: 'library',
          priority: 'low',
          status: 'resolved',
          created_at: '2025-08-26T14:30:00Z'
        }
      ];
      setTickets(mockTickets);
      setFilteredTickets(mockTickets);
    } finally {
      setTicketsLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([loadProfile(), loadTickets()]);
      setLoading(false);
    };
    loadData();
  }, []);

  useEffect(() => {
    if (statusFilter === 'all') {
      setFilteredTickets(tickets);
    } else {
      setFilteredTickets(tickets.filter(ticket => ticket.status === statusFilter));
    }
  }, [statusFilter, tickets]);

  const handleRefreshTickets = () => {
    loadTickets();
  };

  const handleQuickAction = (intent: Intent) => {
    setSmartFormModal({ isOpen: true, intent });
  };

  const handleFormDone = (result: any) => {
    setSmartFormModal({ isOpen: false, intent: null });
    toast({
      title: 'Success',
      description: result.message || 'Action completed successfully',
    });
    // Reload tickets if it was a ticket-related action
    if (smartFormModal.intent === 'create_glpi_ticket') {
      loadTickets();
    }
  };

  const handleFormCancel = () => {
    setSmartFormModal({ isOpen: false, intent: null });
  };

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: 'default' | 'secondary' | 'destructive' | 'outline' } = {
      open: 'default',
      in_progress: 'secondary',
      resolved: 'outline',
      closed: 'destructive'
    };
    return <Badge variant={variants[status] || 'default'}>{status.replace('_', ' ')}</Badge>;
  };

  const getPriorityBadge = (priority: string) => {
    const variants: { [key: string]: 'default' | 'secondary' | 'destructive' } = {
      low: 'secondary',
      normal: 'default',
      high: 'destructive',
      urgent: 'destructive'
    };
    return <Badge variant={variants[priority] || 'default'}>{priority}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading your information...</span>
        </div>
      </div>
    );
  }

  return (
    <UserLayout>
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Self-Service Portal</h1>
          <Button
            onClick={handleRefreshTickets}
            variant="outline"
            size="sm"
            disabled={ticketsLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${ticketsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Student ID</p>
              <p className="text-lg font-semibold">{profile?.student_id || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-lg">{profile?.name || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Major</p>
              <p className="text-lg">{profile?.major || 'Unknown'}</p>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              onClick={() => handleQuickAction('reset_password')}
              variant="outline"
              className="w-full justify-start"
            >
              <Key className="h-4 w-4 mr-2" />
              Reset Password
            </Button>
            <Button
              onClick={() => handleQuickAction('renew_library_card')}
              variant="outline"
              className="w-full justify-start"
            >
              <BookOpen className="h-4 w-4 mr-2" />
              Renew Library Card
            </Button>
            <Button
              onClick={() => handleQuickAction('book_room')}
              variant="outline"
              className="w-full justify-start"
            >
              <CalendarCheck className="h-4 w-4 mr-2" />
              Book Study Room
            </Button>
          </CardContent>
        </Card>

        {/* Tickets Summary Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              Tickets Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {tickets.filter(t => t.status === 'open').length}
                </p>
                <p className="text-sm text-muted-foreground">Open</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {tickets.filter(t => t.status === 'resolved').length}
                </p>
                <p className="text-sm text-muted-foreground">Resolved</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {tickets.filter(t => t.status === 'in_progress').length}
                </p>
                <p className="text-sm text-muted-foreground">In Progress</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">
                  {tickets.length}
                </p>
                <p className="text-sm text-muted-foreground">Total</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              My Tickets
            </CardTitle>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {ticketsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading tickets...
            </div>
          ) : filteredTickets.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No tickets found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTickets.map((ticket) => (
                  <TableRow key={ticket.id}>
                    <TableCell className="font-medium">#{ticket.id}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{ticket.subject}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{ticket.category}</Badge>
                    </TableCell>
                    <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                    <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                    <TableCell>{formatDate(ticket.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Smart Form Modal */}
      <Dialog open={smartFormModal.isOpen} onOpenChange={(open) => {
        if (!open) handleFormCancel();
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {smartFormModal.intent?.replace('_', ' ').toUpperCase()} Form
            </DialogTitle>
          </DialogHeader>
          {smartFormModal.intent && (
            <SmartForm
              intent={smartFormModal.intent}
              context={smartFormModal.context}
              onDone={handleFormDone}
              onCancel={handleFormCancel}
            />
          )}
        </DialogContent>
      </Dialog>
      </div>
    </UserLayout>
  );
};
