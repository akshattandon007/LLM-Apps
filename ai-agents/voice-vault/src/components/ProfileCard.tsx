import { VoiceProfile } from '@/lib/store';
import Link from 'next/link';

interface ProfileCardProps {
  profile: VoiceProfile;
  onDelete?: (id: string) => void;
}

export default function ProfileCard({ profile, onDelete }: ProfileCardProps) {
  const totalDuration = profile.samples.reduce((sum, s) => sum + s.duration, 0);
  const hasVoice = !!profile.voiceId;
  const initial = profile.name.charAt(0).toUpperCase();

  return (
    <div className="card bg-base-100 shadow-sm border border-base-300 rounded-box hover:shadow-md transition-shadow">
      <div className="card-body p-5">
        {/* Avatar row */}
        <div className="flex items-center gap-4 mb-3">
          <div className="avatar placeholder">
            <div className="w-14 rounded-full bg-primary text-primary-content text-xl font-bold">
              {initial}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="card-title text-lg truncate">{profile.name}</h3>
            <p className="text-sm text-base-content/60">
              {profile.samples.length} recording{profile.samples.length !== 1 ? 's' : ''}
              {' · '}
              {Math.floor(totalDuration / 60)}m {Math.floor(totalDuration % 60)}s
            </p>
          </div>
          {hasVoice && (
            <span className="badge badge-soft badge-success badge-sm">Voice cloned</span>
          )}
        </div>

        {/* Sample captions */}
        {profile.samples.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {profile.samples.map((s) => (
              <span key={s.id} className="badge badge-soft badge-ghost badge-sm truncate max-w-40">
                {s.caption || 'Untitled'}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="card-actions justify-between">
          <Link
            href={`/profile/${profile.id}`}
            className="btn btn-primary btn-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            Ask a question
          </Link>
          {onDelete && (
            <button
              className="btn btn-ghost btn-sm text-error"
              onClick={() => onDelete(profile.id)}
              title="Delete profile"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}