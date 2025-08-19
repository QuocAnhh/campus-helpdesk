import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import AdminPage from './pages/AdminPage';
import ChatLogsPage from './pages/ChatLogsPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/admin/chat-logs" element={<ChatLogsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
