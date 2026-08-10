import { useState } from 'react';

export default function FileUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);

  const handleUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const files = formData.getAll('files');
    if (files.length === 0) return;

    setUploading(true);
    setResults([]);

    try {
      // Upload each file to backend
      const uploadResults = [];
      for (const file of files) {
        const resp = await fetch('/api/proxy/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: file.path || file.name }),
        });
        const data = await resp.json();
        uploadResults.push(data);
      }
      setResults(uploadResults);
      if (onUploadComplete) onUploadComplete();
    } catch (err) {
      setResults([{ message: `Upload failed: ${err.message}` }]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Upload Medical Records</h2>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          name="files"
          multiple
          accept=".pdf,.txt,.jpg,.jpeg,.png"
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-3"
        />
        <button type="submit" disabled={uploading} className="btn-primary">
          {uploading ? 'Uploading...' : 'Upload & Index'}
        </button>
      </form>
      {results.length > 0 && (
        <div className="mt-3 text-sm">
          {results.map((r, i) => (
            <p key={i} className="text-green-700">{r.message || r.detail}</p>
          ))}
        </div>
      )}
    </div>
  );
}