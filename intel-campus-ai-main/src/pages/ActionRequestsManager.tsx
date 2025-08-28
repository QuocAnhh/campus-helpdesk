import React, { useState, useEffect } from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { 
  Loader2, 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Eye, 
  Edit,
  Filter,
  RefreshCw,
  User,
  Calendar,
  AlertCircle,
  Search,
  Settings,
  Key,
  BookOpen,
  CalendarDays,
  HelpCircle,
  Home
} from 'lucide-react';
import {
  ActionRequest,
  ActionRequestStats,
  getActionRequests,
  getActionRequestStats,
  updateActionRequest
} from '@/services/admin';

const ActionRequestsManager: React.FC = () => {
  const [requests, setRequests] = useState<ActionRequest[]>([]);
  const [filteredRequests, setFilteredRequests] = useState<ActionRequest[]>([]);
  const [stats, setStats] = useState<ActionRequestStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedRequest, setSelectedRequest] = useState<ActionRequest | null>(null);
  const [detailsModal, setDetailsModal] = useState(false);
  const [processingModal, setProcessingModal] = useState(false);
  const [notes, setNotes] = useState('');
  const [newStatus, setNewStatus] = useState('in_progress');
  const { toast } = useToast();

  const loadRequests = async () => {
    setLoading(true);
    try {
      const [requestsData, statsData] = await Promise.all([
        getActionRequests({
          status: statusFilter !== 'all' ? statusFilter : undefined,
          action_type: typeFilter !== 'all' ? typeFilter : undefined,
          limit: 100
        }),
        getActionRequestStats()
      ]);
      
      setRequests(requestsData);
      setFilteredRequests(requestsData);
      setStats(statsData);
    } catch (error: any) {
      console.error('Failed to load action requests:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load action requests',
        variant: 'destructive',
      });
      
      const mockRequests: ActionRequest[] = [
        {
          id: 1,
          student_id: 'student123',
          action_type: 'reset_password',
          status: 'submitted',
          request_data: { student_id: 'student123' },
          submitted_at: '2025-08-28T10:00:00Z'
        }
      ];
      setRequests(mockRequests);
      setFilteredRequests(mockRequests);
      setStats({
        total: 1,
        submitted: 1,
        in_progress: 0,
        completed: 0,
        failed: 0,
        cancelled: 0
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, []);

  useEffect(() => {
    let filtered = requests;
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(req => req.status === statusFilter);
    }
    
    if (typeFilter !== 'all') {
      filtered = filtered.filter(req => req.action_type === typeFilter);
    }
    
    if (searchTerm) {
      filtered = filtered.filter(req => 
        req.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.action_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (req.external_id && req.external_id.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    setFilteredRequests(filtered);
  }, [requests, statusFilter, typeFilter, searchTerm]);

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: string } = {
      submitted: 'bg-orange-100 text-orange-800 border-orange-200',
      in_progress: 'bg-blue-100 text-blue-800 border-blue-200',
      completed: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200',
      cancelled: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    return (
      <Badge className={`${variants[status] || variants.submitted} border`}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  const getActionIcon = (actionType: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      reset_password: <Key className="h-4 w-4" />,
      renew_library_card: <BookOpen className="h-4 w-4" />,
      book_room: <CalendarDays className="h-4 w-4" />,
      create_glpi_ticket: <HelpCircle className="h-4 w-4" />,
      request_dorm_fix: <Home className="h-4 w-4" />
    };
    return icons[actionType] || <Settings className="h-4 w-4" />;
  };

  const getActionTypeLabel = (actionType: string) => {
    const labels: { [key: string]: string } = {
      reset_password: 'Reset Password',
      renew_library_card: 'Renew Library Card',
      book_room: 'Book Room',
      create_glpi_ticket: 'Create GLPI Ticket',
      request_dorm_fix: 'Request Dorm Fix'
    };
    return labels[actionType] || actionType;
  };

  const handleUpdateStatus = async (requestId: number, status: string, notes: string) => {
    try {
      await updateActionRequest(requestId, { status, notes, processed_by: 'admin' });
      
      // Update local state
      setRequests(prev => prev.map(req => 
        req.id === requestId 
          ? { ...req, status, notes, processed_by: 'admin' }
          : req
      ));
      
      toast({
        title: 'Success',
        description: 'Request status updated successfully',
      });
      
      setProcessingModal(false);
      setSelectedRequest(null);
      setNotes('');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update request status',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
            <div>
              <h3 className="text-lg font-semibold">Loading Action Requests</h3>
              <p className="text-muted-foreground">Please wait while we fetch the data...</p>
            </div>
          </div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">Action Requests</h1>
            <p className="text-muted-foreground">
              Manage and monitor student self-service requests
            </p>
          </div>
          <Button onClick={loadRequests} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-6">
          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total || 0}</div>
              <p className="text-xs text-muted-foreground">All requests</p>
            </CardContent>
          </Card>
          
          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Submitted</CardTitle>
              <AlertCircle className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats?.submitted || 0}</div>
              <p className="text-xs text-muted-foreground">Awaiting review</p>
            </CardContent>
          </Card>
          
          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats?.in_progress || 0}</div>
              <p className="text-xs text-muted-foreground">Being processed</p>
            </CardContent>
          </Card>

          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats?.completed || 0}</div>
              <p className="text-xs text-muted-foreground">Successfully done</p>
            </CardContent>
          </Card>

          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Failed</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats?.failed || 0}</div>
              <p className="text-xs text-muted-foreground">Error occurred</p>
            </CardContent>
          </Card>

          <Card className="col-span-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Cancelled</CardTitle>
              <XCircle className="h-4 w-4 text-gray-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">{stats?.cancelled || 0}</div>
              <p className="text-xs text-muted-foreground">User cancelled</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters & Search
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by student ID, action type, or external ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-80"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium">Status:</label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="submitted">Submitted</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium">Type:</label>
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-52">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="reset_password">Reset Password</SelectItem>
                    <SelectItem value="renew_library_card">Renew Library Card</SelectItem>
                    <SelectItem value="book_room">Book Room</SelectItem>
                    <SelectItem value="create_glpi_ticket">Create GLPI Ticket</SelectItem>
                    <SelectItem value="request_dorm_fix">Request Dorm Fix</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Showing {filteredRequests.length} of {requests.length} requests
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Requests Table */}
        <Card>
          <CardHeader>
            <CardTitle>Action Requests ({filteredRequests.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {filteredRequests.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold">No requests found</h3>
                <p className="text-muted-foreground">
                  {requests.length === 0 ? 'No action requests have been submitted yet.' : 'No requests match your current filters.'}
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Student</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Processed By</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRequests.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell className="font-medium">#{request.id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          {request.student_id}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getActionIcon(request.action_type)}
                          <span className="font-medium">{getActionTypeLabel(request.action_type)}</span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(request.status)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {new Date(request.submitted_at).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell>{request.processed_by || '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedRequest(request);
                              setDetailsModal(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {request.status === 'submitted' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedRequest(request);
                                setProcessingModal(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Details Modal */}
        <Dialog open={detailsModal} onOpenChange={setDetailsModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Request Details #{selectedRequest?.id}</DialogTitle>
            </DialogHeader>
            {selectedRequest && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium">Student ID</h4>
                    <p>{selectedRequest.student_id}</p>
                  </div>
                  <div>
                    <h4 className="font-medium">Action Type</h4>
                    <p>{getActionTypeLabel(selectedRequest.action_type)}</p>
                  </div>
                  <div>
                    <h4 className="font-medium">Status</h4>
                    {getStatusBadge(selectedRequest.status)}
                  </div>
                  <div>
                    <h4 className="font-medium">Submitted</h4>
                    <p>{new Date(selectedRequest.submitted_at).toLocaleString()}</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Request Data</h4>
                  <pre className="bg-muted p-3 rounded text-sm overflow-auto">
                    {JSON.stringify(selectedRequest.request_data, null, 2)}
                  </pre>
                </div>
                
                {selectedRequest.result_data && (
                  <div>
                    <h4 className="font-medium mb-2">Result Data</h4>
                    <pre className="bg-muted p-3 rounded text-sm overflow-auto">
                      {JSON.stringify(selectedRequest.result_data, null, 2)}
                    </pre>
                  </div>
                )}
                
                {selectedRequest.notes && (
                  <div>
                    <h4 className="font-medium mb-2">Notes</h4>
                    <p className="bg-muted p-3 rounded">{selectedRequest.notes}</p>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Processing Modal */}
        <Dialog open={processingModal} onOpenChange={setProcessingModal}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Update Request #{selectedRequest?.id}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Update Status</label>
                <Select value={newStatus} onValueChange={setNewStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Notes</label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about processing this request..."
                  rows={3}
                />
              </div>
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setProcessingModal(false)}>
                  Cancel
                </Button>
                <Button onClick={() => handleUpdateStatus(selectedRequest?.id!, newStatus, notes)}>
                  Update Request
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
};

export default ActionRequestsManager;
