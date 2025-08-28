import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import ChatLogsPage from "./pages/ChatLogsPage";
import TicketsPage from "./pages/TicketsPage";
import ActionRequestsManager from "./pages/ActionRequestsManager";
import { SelfService } from "./pages/SelfService";
import SmartFormDemo from "./pages/SmartFormDemo";
import NotFound from "./pages/NotFound";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { PrivateRoute, AdminRoute } from "./components/ProtectedRoutes";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<ChatPage />} />
            <Route path="/tickets" element={<TicketsPage />} />
            <Route path="/self-service" element={<SelfService />} />
            <Route path="/demo/smart-form" element={<SmartFormDemo />} />
          </Route>

          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/admin/chat-logs" element={<ChatLogsPage />} />
            <Route path="/admin/action-requests" element={<ActionRequestsManager />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
