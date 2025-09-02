import React, { useState } from 'react';
import { VoiceChat } from '@/components/chat/VoiceChat';

export default function VoiceChatPage() {
  const [sessionId, setSessionId] = useState<string>();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Voice Chat Demo
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Thử nghiệm tính năng chat giọng nói với Campus Helpdesk AI. 
            Nhấn vào nút micro để bắt đầu ghi âm, hệ thống sẽ tự động 
            nhận diện giọng nói tiếng Việt và trả lời bằng giọng nói.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <VoiceChat
            sessionId={sessionId}
            onSessionChange={setSessionId}
            className="h-[600px]"
          />
        </div>

        {/* Chat History Toggle */}
        <div className="mt-8 text-center">
          <div className="inline-flex items-center space-x-4 bg-white rounded-lg p-4 shadow-sm">
            <span className="text-sm text-gray-600">Session ID:</span>
            <code className="bg-gray-100 px-2 py-1 rounded text-sm">
              {sessionId || 'Chưa có session'}
            </code>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">
            Hướng dẫn sử dụng:
          </h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div className="space-y-2">
              <h4 className="font-medium">📱 Yêu cầu hệ thống:</h4>
              <ul className="space-y-1 list-disc list-inside ml-4">
                <li>Trình duyệt hỗ trợ WebRTC (Chrome, Firefox, Safari)</li>
                <li>Cho phép truy cập microphone</li>
                <li>Kết nối internet ổn định</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">🎤 Cách sử dụng:</h4>
              <ul className="space-y-1 list-disc list-inside ml-4">
                <li>Nhấn nút micro để bắt đầu ghi âm</li>
                <li>Nói câu hỏi rõ ràng bằng tiếng Việt</li>
                <li>Nhấn lại để dừng và xử lý</li>
                <li>Nghe phản hồi tự động từ hệ thống</li>
              </ul>
            </div>
          </div>
        </div>

        {/* API Keys Notice */}
        <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 text-yellow-800">
            <span className="text-sm font-medium">⚠️ Lưu ý:</span>
            <span className="text-sm">
              Cần cấu hình OPENAI_API_KEY và ELEVENLABS_API_KEY trong file .env để sử dụng tính năng này.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
