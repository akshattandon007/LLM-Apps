import { useState } from "react";

interface RewriteOutputProps {
  original: string;
  rewritten: string;
  personaName: string;
  personaEmoji: string;
  loading: boolean;
  error: string | null;
}

export default function RewriteOutput({
  original,
  rewritten,
  personaName,
  personaEmoji,
  loading,
  error,
}: RewriteOutputProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(rewritten);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: select text for manual copy
      const el = document.getElementById("rewritten-text");
      if (el) {
        const range = document.createRange();
        range.selectNodeContents(el);
        const sel = window.getSelection();
        sel?.removeAllRanges();
        sel?.addRange(range);
      }
    }
  };

  const handleShare = async () => {
    const shareText = `"${rewritten}"\n— Rewritten as ${personaEmoji} ${personaName} by TextPersona`;
    if (navigator.share) {
      try {
        await navigator.share({ text: shareText });
      } catch {}
    } else {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="w-full">
        <h2 className="text-lg font-bold mb-3">Rewritten</h2>
        <div className="card bg-base-200 border border-base-300 p-6 flex items-center justify-center gap-3 animate-fade-in">
          <span className="loading loading-dots loading-md text-primary" />
          <span className="text-base-content/70">
            {personaEmoji} {personaName} is working their magic...
          </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <h2 className="text-lg font-bold mb-3">Rewritten</h2>
        <div className="card bg-error/10 border border-error/30 p-6 animate-fade-in">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-semibold text-error">Something went wrong</p>
              <p className="text-sm text-base-content/70 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!rewritten) {
    return null;
  }

  return (
    <div className="w-full animate-fade-in">
      <h2 className="text-lg font-bold mb-3">
        Rewritten as {personaEmoji} {personaName}
      </h2>
      <div className="card bg-base-200 border border-base-300 overflow-hidden">
        {/* Original */}
        <div className="px-5 pt-4 pb-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
            Original
          </span>
          <p className="text-sm text-base-content/80 mt-1 italic">
            {original}
          </p>
        </div>
        {/* Divider */}
        <div className="border-t border-base-300 mx-5" />
        {/* Rewritten */}
        <div className="px-5 pt-3 pb-4">
          <span className="text-xs font-semibold uppercase tracking-wide text-primary">
            Rewritten
          </span>
          <p
            id="rewritten-text"
            className="text-base mt-1 leading-relaxed whitespace-pre-wrap"
          >
            {rewritten}
          </p>
        </div>
        {/* Actions */}
        <div className="flex gap-2 px-5 pb-4">
          <button
            className="btn btn-sm btn-primary gap-1"
            onClick={handleCopy}
          >
            {copied ? "✅ Copied!" : "📋 Copy"}
          </button>
          <button
            className="btn btn-sm btn-outline gap-1"
            onClick={handleShare}
          >
            📤 Share
          </button>
        </div>
      </div>
    </div>
  );
}
