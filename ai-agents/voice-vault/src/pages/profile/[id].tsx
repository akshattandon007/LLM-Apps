import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import StoryCard from '@/components/StoryCard';
import {
  getProfile,
  getStories,
  saveStory,
  deleteStory,
  VoiceProfile,
  Story,
  generateId,
} from '@/lib/store';

export default function ProfilePage() {
  const router = useRouter();
  const { id } = router.query;
  const [profile, setProfile] = useState<VoiceProfile | null>(null);
  const [stories, setStories] = useState<Story[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (!router.isReady || !id) return;
    setMounted(true);
    const pid = id as string;
    const p = getProfile(pid);
    if (!p) {
      router.push('/');
      return;
    }
    setProfile(p);
    setStories(getStories(pid));
  }, [router.isReady, id, router]);

  // ── Ask a question ───────────────────────────────────────
  async function askQuestion() {
    if (!question.trim() || !profile) return;
    setLoading(true);
    setError(null);

    const storiesForApi = profile.samples.map((s) => ({
      id: s.id,
      caption: s.caption || 'Untitled',
      duration: s.duration,
    }));

    // If no stories with captions, show a warning
    if (storiesForApi.length === 0) {
      setError('No recordings yet. Record some stories first.');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          stories: storiesForApi,
          voiceId: profile.voiceId,
        }),
      });

      const data = await res.json();

      if (!res.ok && data.error) {
        setError(data.error);
        setLoading(false);
        return;
      }

      const story: Story = {
        id: generateId(),
        profileId: profile.id,
        question: question.trim(),
        answerText: data.answerText || 'I couldn\'t think of an answer to that.',
        audioDataUrl: data.audioDataUrl,
        audioMime: data.audioMime,
        matchedCaption: data.matchedCaption,
        createdAt: Date.now(),
      };

      saveStory(story);
      setStories(getStories(profile.id));
      setQuestion('');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Network error';
      setError(`Failed to get answer: ${msg}`);
    } finally {
      setLoading(false);
    }
  }

  // ── Handle Enter key ─────────────────────────────────────
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  }

  // ── Delete a story ───────────────────────────────────────
  function handleDeleteStory(storyId: string) {
    if (confirm('Delete this story?')) {
      deleteStory(storyId);
      setStories(getStories(profile!.id));
    }
  }

  // ── Share a story ────────────────────────────────────────
  function handleShareStory(story: Story) {
    const text = `Q: ${story.question}\nA: "${story.answerText}" — VoiceVault`;
    if (navigator.share) {
      navigator.share({ title: 'VoiceVault', text }).catch(() => {});
    } else {
      navigator.clipboard.writeText(text).catch(() => {});
    }
  }

  // ── Share profile ────────────────────────────────────────
  function shareProfile() {
    const url = `${window.location.origin}/profile/${profile?.id}`;
    const text = `Listen to ${profile?.name}'s voice on VoiceVault — ask questions and hear them answer.`;
    if (navigator.share) {
      navigator.share({ title: `VoiceVault — ${profile?.name}`, text, url }).catch(() => {});
    } else {
      navigator.clipboard.writeText(`${text}\n${url}`).catch(() => {});
    }
  }

  if (!mounted || !profile) return null;

  const totalDuration = profile.samples.reduce((s, smp) => s + smp.duration, 0);

  return (
    <Layout>
      {/* Profile header */}
      <div className="card bg-base-100 border border-base-300 rounded-box p-5 mb-6">
        <div className="flex items-center gap-4">
          <div className="avatar placeholder">
            <div className="w-16 rounded-full bg-primary text-primary-content text-2xl font-bold">
              {profile.name.charAt(0).toUpperCase()}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-base-content truncate">
              {profile.name}
            </h1>
            <p className="text-sm text-base-content/60">
              {profile.samples.length} recording{profile.samples.length !== 1 ? 's' : ''}
              {' · '}
              {Math.floor(totalDuration / 60)}m {Math.floor(totalDuration % 60)}s total
              {profile.voiceId && ' · Voice cloned'}
            </p>
            {/* Sample captions */}
            <div className="flex flex-wrap gap-1 mt-2">
              {profile.samples.map((s) => (
                <span
                  key={s.id}
                  className="badge badge-soft badge-ghost badge-sm truncate max-w-40"
                  title={s.caption || 'No caption'}
                >
                  {s.caption || 'Untitled'}
                </span>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              className="btn btn-ghost btn-sm"
              onClick={shareProfile}
              title="Share this profile"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
              </svg>
            </button>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => router.push(`/record?profile=${profile.id}`)}
              title="Add more recordings"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Ask box */}
      <div className="card bg-base-100 border border-base-300 rounded-box p-4 mb-6">
        <div className="flex gap-3">
          <textarea
            className="textarea textarea-bordered flex-1 resize-none"
            rows={1}
            placeholder={`Ask ${profile.name} something...`}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="btn btn-primary self-end"
            onClick={askQuestion}
            disabled={!question.trim() || loading}
          >
            {loading ? (
              <span className="loading loading-spinner loading-sm" />
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>
        </div>
        {error && (
          <p className="text-error text-sm mt-2">{error}</p>
        )}
        <p className="text-xs text-base-content/40 mt-2">
          Press Enter to ask, Shift+Enter for new line
        </p>
      </div>

      {/* Stories / Q&A list */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-base-content">
          Conversations ({stories.length})
        </h2>
        {stories.length === 0 ? (
          <div className="card bg-base-100 border border-base-300 rounded-box">
            <div className="card-body items-center text-center py-8">
              <div className="text-5xl mb-3 opacity-40">💬</div>
              <p className="text-base-content/60">
                Ask a question above to start a conversation with {profile.name}.
              </p>
            </div>
          </div>
        ) : (
          stories.map((story) => (
            <StoryCard
              key={story.id}
              story={story}
              profileName={profile.name}
              onDelete={handleDeleteStory}
              onShare={handleShareStory}
            />
          ))
        )}
      </div>
    </Layout>
  );
}