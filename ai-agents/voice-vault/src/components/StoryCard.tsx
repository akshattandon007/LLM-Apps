import AudioPlayer from './AudioPlayer';
import { Story } from '@/lib/store';

interface StoryCardProps {
  story: Story;
  profileName: string;
  onDelete?: (id: string) => void;
  onShare?: (story: Story) => void;
}

export default function StoryCard({ story, profileName, onDelete, onShare }: StoryCardProps) {
  return (
    <div className="card bg-base-100 shadow-sm border border-base-300 rounded-box">
      <div className="card-body p-5">
        {/* Question bubble */}
        <div className="chat chat-end mb-2">
          <div className="chat-bubble chat-bubble-primary text-sm">
            {story.question}
          </div>
        </div>

        {/* Matched caption */}
        {story.matchedCaption && (
          <div className="mb-2">
            <span className="badge badge-soft badge-accent text-xs">
              From: {story.matchedCaption}
            </span>
          </div>
        )}

        {/* Answer text */}
        <div className="story-text mb-4">
          &ldquo;{story.answerText}&rdquo;
        </div>

        {/* Audio player */}
        {story.audioDataUrl && (
          <AudioPlayer
            src={story.audioDataUrl}
            mime={story.audioMime}
            className="mb-3"
          />
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-base-content/50">
            {new Date(story.createdAt).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          <div className="flex gap-2">
            {onShare && (
              <button
                className="btn btn-ghost btn-xs"
                onClick={() => onShare(story)}
                title="Share this story"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                </svg>
                Share
              </button>
            )}
            {onDelete && (
              <button
                className="btn btn-ghost btn-xs text-error"
                onClick={() => onDelete(story.id)}
                title="Delete this story"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}