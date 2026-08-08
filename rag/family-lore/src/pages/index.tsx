import { useState, useMemo } from 'react';
import { sampleData, importOptions, Message } from '@/data/sampleData';

/* ───────── helper ───────── */

function initials(name: string): string {
  const parts = name.replace(/<[^>]+>/g, '').trim().split(/\s+/);
  return parts.length > 1
    ? parts[0][0] + parts[parts.length - 1][0]
    : parts[0][0];
}

function highlight(text: string, query: string): JSX.Element[] {
  if (!query.trim()) return [<span key="0">{text}</span>];
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
  return parts.map((p, i) =>
    p.toLowerCase() === query.toLowerCase()
      ? <mark key={i} className="bg-amber-300 dark:bg-amber-600 px-0.5 rounded">{p}</mark>
      : <span key={i}>{p}</span>
  );
}

function formatDate(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
    ' · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function sourceBadgeClass(source: string): string {
  switch (source) {
    case 'whatsapp': return 'badge-success';
    case 'email':    return 'badge-info';
    case 'imessage': return 'badge-warning';
    default:         return 'badge-ghost';
  }
}

/* ───────── components ───────── */

function Sidebar({ onImportClick }: { onImportClick: () => void }) {
  return (
    <aside className="w-full lg:w-64 bg-base-200 min-h-screen flex flex-col p-4 lg:p-6 border-r border-base-300">
      <div className="flex items-center gap-2 mb-8">
        <span className="text-2xl">📖</span>
        <h1 className="text-xl font-bold text-amber-800 dark:text-amber-400">Family Lore</h1>
      </div>

      <button className="btn btn-primary btn-block mb-6 gap-2" onClick={onImportClick}>
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Import Data
      </button>

      <ul className="menu menu-md rounded-box w-full">
        <li className="menu-title text-xs uppercase tracking-wider text-base-content/60">Navigation</li>
        <li>
          <a className="active bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 font-medium">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            All Messages
            <span className="badge badge-sm ml-auto">{sampleData.length}</span>
          </a>
        </li>
      </ul>

      <div className="mt-auto pt-4 border-t border-base-300">
        <div className="text-xs text-base-content/50">Family Lore v0.1.0</div>
      </div>
    </aside>
  );
}

function HeroSection() {
  return (
    <div className="hero py-10 lg:py-16 px-4">
      <div className="hero-content text-center">
        <div className="max-w-2xl">
          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-4xl">📖</span>
            <h1 className="text-4xl lg:text-5xl font-bold text-amber-800 dark:text-amber-300">
              Family Lore
            </h1>
          </div>
          <p className="text-lg lg:text-xl italic text-base-content/70 mb-2">
            &ldquo;What did Dad say about the roof in 2019? It already knows.&rdquo;
          </p>
          <p className="text-base text-base-content/60 max-w-lg mx-auto">
            Every message, email, and memory in one searchable place.
          </p>
          <div className="divider divider-amber my-6 max-w-xs mx-auto" />
        </div>
      </div>
    </div>
  );
}

function ImportCards({ onStartSearch }: { onStartSearch: () => void }) {
  return (
    <section id="import-section" className="px-4 pb-10">
      <h2 className="text-xl font-semibold text-center mb-6 text-amber-700 dark:text-amber-400">
        Import Your Family Communications
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
        {importOptions.map((opt) => (
          <div key={opt.id} className="card card-border bg-base-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="card-body">
              <div className="text-3xl mb-2">{opt.icon}</div>
              <h3 className="card-title text-base">{opt.title}</h3>
              <p className="text-sm text-base-content/70">{opt.description}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                <span className="badge badge-outline badge-sm">{opt.formats}</span>
                <span className="badge badge-outline badge-sm">Up to {opt.maxSize}</span>
              </div>
              <div className="card-actions mt-4">
                <button className="btn btn-outline btn-sm btn-block gap-2" onClick={startSearch}>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="text-center mt-4">
        <p className="text-sm text-base-content/50">
          Sample data loaded for demo. Upload your own files to replace it.
        </p>
      </div>
    </section>
  );
}

function SearchBar({ query, setQuery, onSearch }: {
  query: string;
  setQuery: (v: string) => void;
  onSearch: () => void;
}) {
  return (
    <div className="px-4 max-w-3xl mx-auto w-full">
      <div className="join w-full">
        <div className="join-item flex-1 relative">
          <textarea
            className="textarea textarea-bordered w-full pr-12 resize-none min-h-[3.5rem] max-h-32 leading-relaxed"
            placeholder="Ask anything... e.g. &quot;What did Dad say about the roof?&quot; or &quot;Trip budget discussions&quot;"
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSearch(); } }}
          />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 absolute right-4 top-1/2 -translate-y-1/2 text-base-content/40 pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <button className="btn btn-primary join-item" onClick={onSearch}>
          Search
        </button>
      </div>
    </div>
  );
}

function MessageCard({ msg, q }: { msg: Message; q: string }) {
  const [open, setOpen] = useState(false);
  const hasThread = msg.thread && msg.thread.length > 0;

  return (
    <div className="card card-border bg-base-100 shadow-sm">
      <div className="card-body p-4 lg:p-5">
        {/* header row */}
        <div className="flex items-center gap-3 mb-2">
          <div className="avatar placeholder">
            <div className="w-10 h-10 rounded-full bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 text-sm font-bold">
              <span>{initials(msg.sender)}</span>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm truncate">{msg.sender}</div>
            <div className="text-xs text-base-content/50">{formatDate(msg.timestamp)}</div>
          </div>
          <span className={`badge badge-sm ${sourceBadgeClass(msg.source)}`}>
            {msg.source === 'whatsapp' ? 'WhatsApp' : msg.source === 'email' ? 'Email' : 'iMessage'}
          </span>
        </div>

        {msg.group && (
          <div className="text-xs text-base-content/50 mb-2">
            📁 {msg.group}
          </div>
        )}

        {msg.subject && (
          <div className="text-xs font-medium text-base-content/60 mb-1 truncate">
            Subject: {msg.subject}
          </div>
        )}

        <div className="text-sm leading-relaxed">
          {highlight(msg.content, q)}
        </div>

        {/* thread collapse */}
        {hasThread && (
          <div className="mt-3 border-t border-base-200 pt-2">
            <button
              className="btn btn-ghost btn-xs gap-1 text-base-content/60 hover:text-base-content"
              onClick={() => setOpen(!open)}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={`h-4 w-4 transition-transform ${open ? 'rotate-90' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {open ? 'Collapse thread' : `View thread (${msg.thread!.length} more)`}
            </button>

            {open && (
              <div className="mt-2 space-y-3 pl-4 border-l-2 border-amber-300 dark:border-amber-700">
                {msg.thread!.map((reply, i) => (
                  <div key={i} className="text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="avatar placeholder">
                        <div className="w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 text-[10px] font-bold">
                          <span>{initials(reply.sender)}</span>
                        </div>
                      </div>
                      <span className="font-medium text-xs">{reply.sender}</span>
                      <span className="text-[10px] text-base-content/40">{formatDate(reply.timestamp)}</span>
                      {reply.subject && (
                        <span className="text-[10px] text-base-content/40 truncate max-w-[120px]">{reply.subject}</span>
                      )}
                    </div>
                    <p className="pl-8">{highlight(reply.content, q)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ───────── Page ───────── */

// Track scrolling to section
function startSearch() {
  const el = document.getElementById('search-section');
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState(false);
  const [showHero, setShowHero] = useState(true);
  const [showImport, setShowImport] = useState(true);

  const results = useMemo(() => {
    if (!query.trim()) return sampleData;
    const q = query.toLowerCase();
    const hits = sampleData.filter((msg) => {
      const mainHit =
        msg.content.toLowerCase().includes(q) ||
        msg.sender.toLowerCase().includes(q) ||
        (msg.group && msg.group.toLowerCase().includes(q)) ||
        (msg.subject && msg.subject.toLowerCase().includes(q));
      const threadHit = msg.thread?.some(
        (r) =>
          r.content.toLowerCase().includes(q) ||
          r.sender.toLowerCase().includes(q)
      );
      return mainHit || threadHit;
    });
    return hits.length > 0 ? hits : [];
  }, [query, searched]);

  function handleSearch() {
    setSearched(true);
    setShowHero(false);
    setShowImport(false);
    // scroll to results
    setTimeout(() => {
      document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }

  function handleImportClick() {
    setShowImport(true);
    setShowHero(false);
    setTimeout(() => {
      document.getElementById('import-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }

  return (
    <div className="drawer lg:drawer-open">
      <input id="sidebar-drawer" type="checkbox" className="drawer-toggle" />
      <div className="drawer-content flex flex-col min-h-screen">
        {/* mobile navbar with hamburger */}
        <div className="navbar bg-base-200 lg:hidden sticky top-0 z-30 shadow-sm">
          <div className="flex-none">
            <label htmlFor="sidebar-drawer" className="btn btn-square btn-ghost">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="inline-block h-6 w-6 stroke-current">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </label>
          </div>
          <div className="flex-1">
            <span className="text-lg font-bold text-amber-800 dark:text-amber-400">📖 Family Lore</span>
          </div>
          <button className="btn btn-primary btn-sm" onClick={handleImportClick}>
            Import
          </button>
        </div>

        {/* main content */}
        <main className="flex-1">
          {/* Hero */}
          {showHero && <HeroSection />}

          {/* Import cards */}
          {showImport && <ImportCards onStartSearch={startSearch} />}

          {/* Search bar (always visible) */}
          <section id="search-section" className="py-6 lg:py-10">
            <SearchBar query={query} setQuery={setQuery} onSearch={handleSearch} />
          </section>

          {/* Results */}
          {searched && (
            <section id="results-section" className="px-4 pb-10">
              <div className="max-w-3xl mx-auto">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-base-content/80">
                    {results.length > 0
                      ? `Found ${results.length} result${results.length > 1 ? 's' : ''}`
                      : 'No results found'}
                  </h2>
                  {results.length > 0 && (
                    <span className="text-xs text-base-content/40">
                      Search limited to sample data
                    </span>
                  )}
                </div>

                {results.length > 0 ? (
                  <div className="space-y-3">
                    {results.map((msg) => (
                      <MessageCard key={msg.id} msg={msg} q={query} />
                    ))}
                  </div>
                ) : (
                  <div className="card card-border bg-base-200">
                    <div className="card-body items-center text-center py-12">
                      <span className="text-4xl mb-3">🔍</span>
                      <p className="text-base-content/60">
                        Nothing matches &ldquo;{query}&rdquo;. Try different keywords or browse all messages.
                      </p>
                      <button
                        className="btn btn-ghost btn-sm mt-2"
                        onClick={() => { setQuery(''); setSearched(true); }}
                      >
                        Show all messages
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* If no search yet but data is loaded, show all messages hint */}
          {!searched && (
            <section className="px-4 pb-10">
              <div className="max-w-3xl mx-auto text-center">
                <p className="text-sm text-base-content/40">
                  {sampleData.length} messages loaded. Type a query above and hit Search.
                </p>
              </div>
            </section>
          )}
        </main>
      </div>

      {/* sidebar */}
      <div className="drawer-side z-40">
        <label htmlFor="sidebar-drawer" className="drawer-overlay" />
        <Sidebar onImportClick={handleImportClick} />
      </div>
    </div>
  );
}