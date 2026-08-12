// ── Types ────────────────────────────────────────────────────

export interface VoiceSample {
  id: string;
  caption: string;      // e.g. "The first car I owned"
  dataUrl: string;      // base64 data URL of the audio
  mime: string;         // audio/webm
  duration: number;     // seconds
  createdAt: number;
}

export interface VoiceProfile {
  id: string;
  name: string;         // e.g. "Grandma Helen"
  voiceId?: string;     // ElevenLabs cloned voice ID
  samples: VoiceSample[];
  createdAt: number;
}

export interface Story {
  id: string;
  profileId: string;
  question: string;
  answerText: string;
  audioDataUrl?: string; // base64 audio from TTS
  audioMime?: string;
  matchedCaption?: string;
  createdAt: number;
}

// ── Keys ─────────────────────────────────────────────────────

const PROFILES_KEY = 'voicevault.profiles';
const STORIES_KEY = 'voicevault.stories';
const THEME_KEY = 'voicevault.theme';

// ── Helpers ──────────────────────────────────────────────────

function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

function getItem<T>(key: string, fallback: T): T {
  if (!isBrowser()) return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function setItem<T>(key: string, value: T): void {
  if (!isBrowser()) return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn(`VoiceVault: localStorage write failed for ${key}`, e);
  }
}

// ── Profiles ─────────────────────────────────────────────────

export function loadProfiles(): VoiceProfile[] {
  return getItem<VoiceProfile[]>(PROFILES_KEY, []);
}

export function saveProfiles(profiles: VoiceProfile[]): void {
  setItem(PROFILES_KEY, profiles);
}

export function getProfile(id: string): VoiceProfile | undefined {
  return loadProfiles().find((p) => p.id === id);
}

export function upsertProfile(profile: VoiceProfile): void {
  const profiles = loadProfiles();
  const idx = profiles.findIndex((p) => p.id === profile.id);
  if (idx >= 0) {
    profiles[idx] = profile;
  } else {
    profiles.push(profile);
  }
  saveProfiles(profiles);
}

export function deleteProfile(id: string): void {
  const profiles = loadProfiles().filter((p) => p.id !== id);
  saveProfiles(profiles);
  // Also clean up associated stories
  const stories = loadStories().filter((s) => s.profileId !== id);
  saveStories(stories);
}

export function createProfile(name: string): VoiceProfile {
  const profile: VoiceProfile = {
    id: crypto.randomUUID(),
    name,
    samples: [],
    createdAt: Date.now(),
  };
  upsertProfile(profile);
  return profile;
}

export function addSample(profileId: string, sample: Omit<VoiceSample, 'id' | 'createdAt'>): VoiceSample | null {
  const profile = getProfile(profileId);
  if (!profile) return null;
  const sampleWithId: VoiceSample = {
    ...sample,
    id: crypto.randomUUID(),
    createdAt: Date.now(),
  };
  profile.samples.push(sampleWithId);
  upsertProfile(profile);
  return sampleWithId;
}

export function removeSample(profileId: string, sampleId: string): void {
  const profile = getProfile(profileId);
  if (!profile) return;
  profile.samples = profile.samples.filter((s) => s.id !== sampleId);
  upsertProfile(profile);
}

export function renameProfile(profileId: string, name: string): void {
  const profile = getProfile(profileId);
  if (!profile) return;
  profile.name = name;
  upsertProfile(profile);
}

export function setProfileVoiceId(profileId: string, voiceId: string): void {
  const profile = getProfile(profileId);
  if (!profile) return;
  profile.voiceId = voiceId;
  upsertProfile(profile);
}

// ── Stories ──────────────────────────────────────────────────

export function loadStories(): Story[] {
  return getItem<Story[]>(STORIES_KEY, []);
}

export function saveStories(stories: Story[]): void {
  setItem(STORIES_KEY, stories);
}

export function getStories(profileId?: string): Story[] {
  const all = loadStories();
  return profileId ? all.filter((s) => s.profileId === profileId) : all;
}

export function saveStory(story: Story): void {
  const stories = loadStories();
  stories.unshift(story); // newest first
  // Cap at 50 stories total to stay under storage limits
  const capped = stories.slice(0, 50);
  saveStories(capped);
}

export function deleteStory(id: string): void {
  const stories = loadStories().filter((s) => s.id !== id);
  saveStories(stories);
}

// ── Theme ────────────────────────────────────────────────────

export function getStoredTheme(): 'light' | 'dark' {
  if (!isBrowser()) return 'light';
  return (localStorage.getItem(THEME_KEY) as 'light' | 'dark') || 'light';
}

export function setStoredTheme(theme: 'light' | 'dark'): void {
  if (!isBrowser()) return;
  localStorage.setItem(THEME_KEY, theme);
  document.documentElement.dataset.theme = theme === 'dark' ? 'warmdark' : 'warmlight';
}

// ── ID generator ─────────────────────────────────────────────

export function generateId(): string {
  return crypto.randomUUID();
}