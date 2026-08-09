import { useState, useRef } from 'react';

export default function FileUpload({ onUpload, loading }) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onUpload(files[0]);
    }
  }

  function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      onUpload(files[0]);
      e.target.value = '';
    }
  }

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Upload Transcript
      </h2>
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-gray-300 hover:border-indigo-300 hover:bg-gray-50'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.srt,.vtt"
          onChange={handleFileSelect}
          className="hidden"
        />
        {loading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-500">Processing...</span>
          </div>
        ) : (
          <>
            <div className="text-3xl mb-2">📄</div>
            <p className="text-sm text-gray-600">
              Drop a transcript here or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-1">
              .txt, .srt, .vtt
            </p>
          </>
        )}
      </div>
    </div>
  );
}