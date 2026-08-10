import FileUpload from '../components/FileUpload';
import ChatPanel from '../components/ChatPanel';

export default function Home() {
  return (
    <div className="chat-container">
      <header className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chart</h1>
        <p className="text-sm text-gray-500">Your personal medical records assistant</p>
      </header>
      <FileUpload />
      <ChatPanel />
    </div>
  );
}