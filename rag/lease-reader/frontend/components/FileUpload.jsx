import React, { useState, useRef } from "react";

export default function FileUpload({ onUploadSuccess, onUploadError }) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState(null);
  const inputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      onUploadError?.("Please select a PDF file.");
      return;
    }

    setFileName(file.name);
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/proxy/ingest", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || `Server error: ${res.status}`);
      }

      onUploadSuccess?.(data);
    } catch (err) {
      onUploadError?.(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleClick = () => inputRef.current?.click();

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`file-upload-zone ${dragOver ? "border-brand-500 bg-brand-50" : ""} ${fileName ? "has-file" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleInputChange}
      />

      {uploading ? (
        <div className="text-gray-500">
          <svg className="animate-spin h-8 w-8 mx-auto mb-2 text-brand-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p>Indexing your lease...</p>
        </div>
      ) : fileName ? (
        <div className="text-green-600">
          <svg className="h-8 w-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="font-medium">{fileName}</p>
          <p className="text-sm text-gray-500 mt-1">Click or drop to re-upload</p>
        </div>
      ) : (
        <div className="text-gray-400">
          <svg className="h-10 w-10 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="font-medium">Drop your lease PDF here</p>
          <p className="text-sm mt-1">or click to browse</p>
        </div>
      )}
    </div>
  );
}