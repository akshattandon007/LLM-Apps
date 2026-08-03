interface DarkModeToggleProps {
  dark: boolean;
  onToggle: () => void;
}

export default function DarkModeToggle({ dark, onToggle }: DarkModeToggleProps) {
  return (
    <button
      className="btn btn-circle btn-ghost"
      onClick={onToggle}
      aria-label="Toggle dark mode"
    >
      {dark ? <span className="text-xl">☀️</span> : <span className="text-xl">🌙</span>}
    </button>
  );
}
