import { KeyboardEvent } from "react";

interface MessageInputProps {
  message: string;
  setMessage: (msg: string) => void;
  disabled: boolean;
}

export default function MessageInput({
  message,
  setMessage,
  disabled,
}: MessageInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && message.trim()) {
      e.preventDefault();
      // Submit is triggered by clicking a persona card, so we just prevent
      // accidental newline. The user must still click a persona to rewrite.
    }
  };

  return (
    <div className="w-full">
      <h2 className="text-lg font-bold mb-3">Your Message</h2>
      <textarea
        className="textarea textarea-bordered w-full text-base resize-none"
        rows={3}
        placeholder="Type what you want to say and pick a persona below..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        maxLength={500}
      />
      <div className="flex justify-between items-center mt-1">
        <span className="text-xs text-base-content/50">
          {message.length}/500
        </span>
        {message.trim() && (
          <button
            className="btn btn-ghost btn-xs"
            onClick={() => setMessage("")}
            disabled={disabled}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
