import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import ProfileCard from '@/components/ProfileCard';
import Link from 'next/link';
import { loadProfiles, VoiceProfile, deleteProfile } from '@/lib/store';

export default function Home() {
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setProfiles(loadProfiles());
    setMounted(true);
  }, []);

  function handleDelete(id: string) {
    if (confirm('Delete this voice profile and all its stories?')) {
      deleteProfile(id);
      setProfiles(loadProfiles());
    }
  }

  // ── Share entire app ─────────────────────────────────────
  function shareApp() {
    const url = window.location.href;
    if (navigator.share) {
      navigator.share({
        title: 'VoiceVault',
        text: 'Keep their voice close. Ask anything. Hear them answer.',
        url,
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(url).catch(() => {});
    }
  }

  if (!mounted) return null;

  return (
    <Layout>
      {/* Hero */}
      <div className="hero bg-base-100 rounded-box mb-8 p-8 border border-base-300">
        <div className="hero-content text-center">
          <div className="max-w-lg">
            <div className="flex justify-center mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-16 h-16 text-primary"
              >
                <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
                <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-8.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold text-base-content mb-2">VoiceVault</h1>
            <p className="text-lg text-base-content/70 mb-6">
              Keep their voice close. Ask anything. Hear them answer.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/record" className="btn btn-primary btn-lg">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                Record a voice
              </Link>
              <button className="btn btn-ghost btn-lg" onClick={shareApp}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z" />
                </svg>
                Share VoiceVault
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Library */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-base-content">
            Your voice profiles
          </h2>
          <Link href="/record" className="btn btn-primary btn-sm">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Add a voice
          </Link>
        </div>

        {profiles.length === 0 ? (
          <div className="card bg-base-100 border border-base-300 rounded-box">
            <div className="card-body items-center text-center py-12">
              <div className="text-6xl mb-4 opacity-40">🎙️</div>
              <h3 className="text-lg font-semibold text-base-content/70">No voice profiles yet</h3>
              <p className="text-sm text-base-content/50 max-w-md mb-4">
                Record 3-5 short voice samples from a loved one — their stories, their memories.
                Then ask any question and hear them answer in their own voice.
              </p>
              <Link href="/record" className="btn btn-primary">
                Record your first voice
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map((profile) => (
              <ProfileCard
                key={profile.id}
                profile={profile}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </section>
    </Layout>
  );
}