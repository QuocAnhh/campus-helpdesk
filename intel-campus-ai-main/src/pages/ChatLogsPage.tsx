import { useState, useEffect } from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, Clock, User, Bot, Eye, CheckCircle, RotateCcw } from 'lucide-react';
import { chatAPI } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

const ChatLogsPage = () => {
  const [chatLogs, setChatLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  const [logDetail, setLogDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const fetchChatLogs = async () => {
      try {
        const data = await chatAPI.getChatLogs();
        setChatLogs(data.logs || []);
      } catch (error) {
        console.error('Error fetching chat logs:', error);
        toast({
          title: "Lỗi tải dữ liệu",
          description: "Không thể tải chat logs. Vui lòng thử lại.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchChatLogs();
  }, [toast]);

  const handleViewDetail = async (sessionId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await chatAPI.getChatLogDetail(sessionId);
      setLogDetail(detail);
      setSelectedLog(chatLogs.find(log => log.session_id === sessionId));
    } catch (error) {
      console.error('Error fetching chat detail:', error);
      toast({
        title: "Lỗi",
        description: "Không thể tải chi tiết chat log.",
        variant: "destructive",
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleMarkComplete = async (sessionId: string) => {
    try {
      await chatAPI.markSessionComplete(sessionId);
      toast({
        title: "Thành công",
        description: "Đã đánh dấu session hoàn thành.",
      });
      // Refresh data
      const data = await chatAPI.getChatLogs();
      setChatLogs(data.logs || []);
    } catch (error) {
      console.error('Error marking complete:', error);
      toast({
        title: "Lỗi",
        description: "Không thể đánh dấu session hoàn thành.",
        variant: "destructive",
      });
    }
  };

  const handleReopen = async (sessionId: string) => {
    try {
      await chatAPI.reopenSession(sessionId);
      toast({
        title: "Thành công",
        description: "Đã mở lại session.",
      });
      // Refresh data
      const data = await chatAPI.getChatLogs();
      setChatLogs(data.logs || []);
    } catch (error) {
      console.error('Error reopening session:', error);
      toast({
        title: "Lỗi",
        description: "Không thể mở lại session.",
        variant: "destructive",
      });
    }
  };

  const formatDuration = (start: number, end: number | null) => {
    if (!end) return 'Đang diễn ra';
    const diff = (end - start) * 1000; // Convert to milliseconds
    const minutes = Math.floor(diff / 60000);
    return `${minutes} phút`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-secondary text-secondary-foreground';
      case 'active':
        return 'bg-accent text-accent-foreground';
      case 'error':
        return 'bg-destructive text-destructive-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <AdminLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Chat Logs</h1>
          <p className="text-muted-foreground">
            Xem lịch sử các cuộc hội thoại giữa sinh viên và hệ thống
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tổng phiên chat</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">{chatLogs.length}</span>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Phiên đang hoạt động</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {chatLogs.filter(log => log.status === 'active').length}
              </span>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tổng tin nhắn</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {chatLogs.reduce((sum, log) => sum + log.messages_count, 0)}
              </span>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sinh viên unique</CardTitle>
              <User className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold">
                {new Set(chatLogs.map(log => log.student_id)).size}
              </span>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Lịch sử Chat</CardTitle>
            <CardDescription>
              Danh sách các phiên chat gần đây
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center justify-between py-4 border-b">
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-3 w-48" />
                    </div>
                    <Skeleton className="h-6 w-16" />
                  </div>
                ))}
              </div>
            ) : chatLogs.length > 0 ? (
              <div className="space-y-4">
                {chatLogs.map((log) => (
                  <div key={log.id} className="flex items-center justify-between py-4 border-b border-border last:border-0">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-4">
                        <span className="font-medium">Sinh viên: {log.student_id}</span>
                        <Badge variant="outline">{log.agent}</Badge>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>{log.messages_count} tin nhắn</span>
                        <span>Thời lượng: {formatDuration(log.start_time, log.end_time)}</span>
                        <span>{new Date(log.start_time * 1000).toLocaleString('vi-VN')}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Session: {log.session_id}
                      </div>
                      {log.last_message && (
                        <div className="text-xs text-muted-foreground">
                          Tin nhắn cuối: {log.last_message}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(log.status)}>
                        {log.status === 'completed' ? 'Hoàn thành' : 
                         log.status === 'active' ? 'Đang hoạt động' : log.status}
                      </Badge>
                      
                      {/* Action buttons */}
                      {log.status === 'active' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleMarkComplete(log.session_id)}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Hoàn thành
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReopen(log.session_id)}
                        >
                          <RotateCcw className="h-4 w-4 mr-1" />
                          Mở lại
                        </Button>
                      )}
                      
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleViewDetail(log.session_id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Xem
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                          <DialogHeader>
                            <DialogTitle>Chi tiết Chat Log</DialogTitle>
                            <DialogDescription>
                              Session ID: {selectedLog?.session_id}
                            </DialogDescription>
                          </DialogHeader>
                          {loadingDetail ? (
                            <div className="space-y-4">
                              {[1,2,3].map(i => (
                                <Skeleton key={i} className="h-16 w-full" />
                              ))}
                            </div>
                          ) : logDetail ? (
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <strong>Sinh viên:</strong> {selectedLog?.student_id}
                                </div>
                                <div>
                                  <strong>Agent:</strong> {selectedLog?.agent}
                                </div>
                                <div>
                                  <strong>Số tin nhắn:</strong> {logDetail.total_messages}
                                </div>
                                <div>
                                  <strong>Trạng thái:</strong> {selectedLog?.status}
                                </div>
                              </div>
                              <div className="border-t pt-4">
                                <h4 className="font-semibold mb-3">Lịch sử hội thoại:</h4>
                                <div className="space-y-3 max-h-96 overflow-y-auto">
                                  {logDetail.messages.map((msg, index) => (
                                    <div key={index} className="space-y-2">
                                      <div className="bg-blue-50 p-3 rounded-lg">
                                        <div className="flex justify-between items-start mb-1">
                                          <strong className="text-blue-700">Sinh viên:</strong>
                                          {msg.timestamp && (
                                            <span className="text-xs text-gray-500">
                                              {new Date(msg.timestamp * 1000).toLocaleString('vi-VN')}
                                            </span>
                                          )}
                                        </div>
                                        <p className="text-gray-800">{msg.user}</p>
                                      </div>
                                      <div className="bg-green-50 p-3 rounded-lg">
                                        <div className="flex justify-between items-start mb-1">
                                          <strong className="text-green-700">
                                            Bot ({msg.agent || 'unknown'}):
                                          </strong>
                                        </div>
                                        <p className="text-gray-800">{msg.bot}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <p>Không thể tải chi tiết chat log.</p>
                          )}
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Chưa có chat logs nào. Hãy thử chat với hệ thống để tạo dữ liệu.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default ChatLogsPage;