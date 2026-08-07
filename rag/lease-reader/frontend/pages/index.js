import React, { useState } from "react";
import FileUpload from "../components/FileUpload";
import ChatPanel from "../components/ChatPanel";

export default function Home() {
  const [leaseIndexed, setLeaseIndexed] = useState(false);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [ingestError, setIngestError] = useState(null);

  const handleUploadSuccess = (data) => {
    setLeaseIndexed(true);
    setIngestStatus(data);
    setIngestError(null);
  };

  const handleUploadError = (error) => {
    setIngestError(error);
    setIngestStatus(null);
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Lease Reader
        </h1>
        <p className="text-gray-500">
          Upload your lease agreement and ask questions in plain English
        </p>
      </header>

      {/* Upload section */}
      <section className="mb-8">
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />

        {ingestStatus && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-700">
            <p className="font-medium">✅ Lease indexed successfully</p>
            <p className="mt-1">
              {ingestStatus.num_chunks} chunks across {ingestStatus.domains_found.length} legal domains:
              <span className="ml-1 text-green-600">
                {ingestStatus.domains_found.join(", ")}
              </span>
            </p>
          </div>
        )}

        {ingestError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            <p className="font-medium">❌ Upload failed</p>
            <p className="mt-1">{ingestError}</p>
          </div>
        )}
      </section>

      {/* Chat section */}
      {leaseIndexed && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <ChatPanel />
        </section>
      )}

      {/* Footer */}
      {!leaseIndexed && (
        <footer className="text-center text-gray-400 text-xs mt-8">
          <p>Lease Reader v0.1.0 &mdash; Your lease data stays on your server.</p>
          <p className="mt-1">
            Always consult a lawyer for legal advice. This tool provides
            informational answers only.
          </p>
        </footer>
      )}
    </div>
  );
}