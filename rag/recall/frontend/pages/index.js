import { useState, useRef, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import ChatPanel from '../components/ChatPanel';

export default function Home() {
  const [meetings, setMeetings] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    fetchMeetings();
  }, []);

  async function fetchMeetings() {
    try {
      const res = await fetch('/api/proxy?endpoint=meetings');
      if (res.ok) {
        const data = await res.json();
        setMeetings(data.meetings || []);
      }
    } catch (e) {
      // Server may not be running yet
    }
  }

  async function handleUpload(file) {
    setLoading(true);
    setStatusMessage(`Uploading ${file.name}...`);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/proxy?endpoint=upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setStatusMessage(`Uploaded! Ingesting...`);
        const ingestRes = await fetch('/api/proxy?endpoint=ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: data.file_path }),
        });
        const ingestData = await ingestRes.json();
        if (ingestRes.ok) {
          setUploadedFiles(prev => [...prev, data.filename]);
          setStatusMessage(`Ingested: ${ingestData.meeting_title} (${ingestData.chunks_created} chunks, ${ingestData.speakers.join(', ')})`);
          fetchMeetings();
        } else {
          setStatusMessage(`Ingest failed: ${ingestData.detail}`);
        }
      } else {
        setStatusMessage(`Upload failed: ${data.detail}`);
      }
    } catch (e) {
      setStatusMessage(`Error: ${e.message}`);
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-indigo-600">Recall</h1>
            <p className="text-sm text-gray-500">Meeting transcript RAG</p>
          </div>
          <div className="flex items-center gap-2">
            {meetings.length > 0 && (
              <span className="text-sm text-gray-500">
                {meetings.length} meeting{meetings.length !== 1 ? 's' : ''} indexed
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-6xl mx-auto w-full p-6 flex gap-6">
        {/* Left panel: File upload */}
        <div className="w-80 flex-shrink-0">
          <FileUpload onUpload={handleUpload} loading={loading} />
          
          {statusMessage && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
              {statusMessage}
            </div>
          )}

          {/* Ingested meetings */}
          {meetings.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Indexed Meetings
              </h3>
              <div className="space-y-2">
                {meetings.map((m, i) => (
                  <div key={i} className="p-3 bg-white border border-gray-200 rounded-lg">
                    <div className="font-medium text-sm">{m.title}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {m.chunks} chunks · {m.speakers?.join(', ') || 'no speakers'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel: Chat */}
        <div className="flex-1">
          <ChatPanel meetings={meetings} />
        </div>
      </main>
    </div>
  );
}