import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import VoiceRecorder from '@/components/VoiceRecorder';
import { createProfile, addSample, getProfile, VoiceProfile, setProfileVoiceId } from '@/lib/store';

interface SampleEntry {
  tempId: string;
  dataUrl: string;
  mime: string;
  duration: number;
  caption: string;
}

export default function RecordPage() {
  const router = useRouter();
  const [profileName, setProfileName] = useState('');
  const [profileId, setProfileId] = useState<string | null>(null);
  const [samples, setSamples] = useState<SampleEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [mounted, setMounted] = useState(false);

  // If editing an existing profile (from ?profile=ID)
  useEffect(() => {
    if (!router.isReady) return;
    setMounted(true);
    const pid = router.query.profile as string | undefined;
    if (pid) {
      const profile = getProfile(pid);
      if (profile) {
        setProfileId(profile.id);
        setProfileName(profile.name);
        setSamples(
          profile.samples.map((s) => ({
            tempId: s.id,
            dataUrl: s.dataUrl,
            mime: s.mime,
            duration: s.duration,
            caption: s.caption,
          })),
        );
      }
    }
  }, [router.isReady, router.query.profile]);

  function handleSave(data: { dataUrl: string; mime: string; duration: number }) {
    setSamples((prev) => [
      ...prev,
      {
        tempId: Math.random().toString(36).slice(2),
        ...data,
        caption: '',
      },
    ]);
  }

  function removeSample(tempId: string) {
    setSamples((prev) => prev.filter((s) => s.tempId !== tempId));
  }

  function updateCaption(tempId: string, caption: string) {
    setSamples((prev) =>
      prev.map((s) => (s.tempId === tempId ? { ...s, caption } : s)),
    );
  }

  async function submitAll() {
    if (!profileName.trim()) return;
    setSaving(true);

    if (profileId) {
      // Append to existing profile
      for (const sample of samples) {
        // Check if this is a new sample (not from the original profile)
        const existing = getProfile(profileId);
        const alreadyExists = existing?.samples.find((s) => s.id === sample.tempId);
        if (!alreadyExists) {
          addSample(profileId, {
            caption: sample.caption,
            dataUrl: sample.dataUrl,
            mime: sample.mime,
            duration: sample.duration,
          });
        }
      }
      router.push(`/profile/${profileId}`);
    } else {
      // Create new profile
      const profile = createProfile(profileName.trim());
      for (const sample of samples) {
        addSample(profile.id, {
          caption: sample.caption,
          dataUrl: sample.dataUrl,
          mime: sample.mime,
          duration: sample.duration,
        });
      }

      // Attempt voice cloning (fire-and-forget — don't block navigation)
      if (process.env.NEXT_PUBLIC_ELEVENLABS_KEY || true) {
        // Only attempt if we have samples and the API key is set
        try {
          const res = await fetch('/api/voice', {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
              name: profileName.trim(),
              samples: samples.map((s) => ({
                dataUrl: s.dataUrl,
                mime: s.mime,
              })),
            }),
          });
          if (res.ok) {
            const data = await res.json();
            if (data.voiceId) {
              setProfileVoiceId(profile.id, data.voiceId);
            }
          }
        } catch {
          // Voice cloning failed — app still works with fallback
        }
      }

      router.push(`/profile/${profile.id}`);
    }
  }

  const canSave = profileName.trim().length > 0 && samples.length > 0;
  const maxSamples = 5;

  if (!mounted) return null;

  return (
    <Layout title="Record a voice">
      {/* Instructions */}
      <div className="alert bg-base-100 border border-base-300 rounded-box mb-6">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 shrink-0 text-primary"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
            clipRule="evenodd"
          />
        </svg>
        <div className="text-sm">
          <strong>Record 3-5 short stories</strong> (30-60 seconds each). Ask your loved one to
          tell a specific memory, then add a short caption so VoiceVault can match questions to
          the right story.
        </div>
      </div>

      {/* Profile name */}
      <div className="card bg-base-100 border border-base-300 rounded-box p-5 mb-6">
        <label className="form-control w-full">
          <div className="label">
            <span className="label-text font-medium">Who is this?</span>
          </div>
          <input
            type="text"
            placeholder="e.g. Grandma Helen"
            className="input input-bordered w-full"
            value={profileName}
            onChange={(e) => setProfileName(e.target.value)}
            disabled={!!profileId}
          />
        </label>
      </div>

      {/* Recorder */}
      {samples.length < maxSamples && (
        <div className="mb-6">
          <VoiceRecorder onSave={handleSave} />
        </div>
      )}

      {/* Recorded samples */}
      {samples.length > 0 && (
        <div className="space-y-3 mb-6">
          <h3 className="font-medium text-base-content">
            Recorded stories ({samples.length}/{maxSamples})
          </h3>
          {samples.map((sample, i) => (
            <div
              key={sample.tempId}
              className="card bg-base-100 border border-base-300 rounded-box p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-sm font-medium text-base-content/70">
                  Story {i + 1}
                </span>
                <button
                  className="btn btn-ghost btn-xs text-error"
                  onClick={() => removeSample(sample.tempId)}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex items-center gap-3 mb-2">
                {/* Play */}
                <button
                  className="btn btn-circle btn-sm btn-ghost"
                  onClick={() => {
                    const a = new Audio(sample.dataUrl);
                    a.play();
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
                <span className="text-xs font-mono text-base-content/60">
                  {Math.floor(sample.duration / 60)}:
                  {String(sample.duration % 60).padStart(2, '0')}
                </span>
              </div>
              <input
                type="text"
                placeholder="What is this story about? (e.g. 'The first car')"
                className="input input-bordered input-sm w-full"
                value={sample.caption}
                onChange={(e) => updateCaption(sample.tempId, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Save button */}
      <div className="flex justify-end">
        <button
          className="btn btn-primary btn-lg"
          disabled={!canSave || saving}
          onClick={submitAll}
        >
          {saving ? (
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
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
          {profileId ? 'Save recordings' : `Save ${profileName || 'voice profile'}`}
        </button>
      </div>
    </Layout>
  );
}