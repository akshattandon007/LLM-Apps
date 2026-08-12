import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getStoredTheme, setStoredTheme } from '@/lib/store';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

export default function Layout({ children, title }: LayoutProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = getStoredTheme();
    setTheme(t);
    setStoredTheme(t);
    setMounted(true);
  }, []);

  function toggleTheme() {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    setStoredTheme(next);
  }

  return (
    <div className="min-h-screen flex flex-col bg-base-200">
      {/* Header */}
      <header className="bg-base-100 border-b border-base-300 sticky top-0 z-30">
        <nav className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-lg font-bold text-base-content no-underline">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-7 h-7 text-primary"
            >
              <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
              <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-8.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
            </svg>
            VoiceVault
          </Link>

          <div className="flex items-center gap-2">
            {mounted && (
              <button
                className="btn btn-circle btn-ghost btn-sm"
                onClick={toggleTheme}
                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              >
                {theme === 'light' ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                  </svg>
                )}
              </button>
            )}
          </div>
        </nav>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">
        {title && (
          <h1 className="text-2xl font-bold text-base-content mb-6">{title}</h1>
        )}
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-base-100 border-t border-base-300 py-4 text-center text-xs text-base-content/50">
        VoiceVault &mdash; an interactive audio keepsake
      </footer>
    </div>
  );
}