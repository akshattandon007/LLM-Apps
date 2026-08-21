import { useState, useEffect } from 'react'
import { transformText, type TransformResult } from '../transform/local-transform'
import TextEditor from './components/TextEditor'
import Comparison from './components/Comparison'
import Settings from './components/Settings'
import '../styles/main.css'

export default function App() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState<TransformResult | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [copied, setCopied] = useState(false)

  // Load incoming text from right-click context menu
  useEffect(() => {
    chrome.runtime.sendMessage({ action: 'getIncomingText' }, (response) => {
      if (response?.text) {
        setInput(response.text)
      }
    })
  }, [])

  const handleClean = () => {
    if (!input.trim()) return
    const output = transformText(input)
    setResult(output)
  }

  const handleCopy = async () => {
    if (!result?.transformed) return
    try {
      await navigator.clipboard.writeText(result.transformed)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for extension context
      const ta = document.createElement('textarea')
      ta.value = result.transformed
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleClear = () => {
    setInput('')
    setResult(null)
    setCopied(false)
  }

  return (
    <div className="relative bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 min-h-[500px]">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <h1 className="text-base font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
          <svg
            className="w-4 h-4"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="16" height="16" rx="3" fill="currentColor" />
            <path
              d="M4 5h8M4 8h6M4 11h7"
              stroke="#fff"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          Claude Clean
        </h1>
        <button
          onClick={() => setShowSettings(true)}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
          title="Settings"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
        </button>
      </header>

      {/* Body */}
      <main className="px-4 py-3 space-y-3">
        <TextEditor value={input} onChange={setInput} />

        {/* Clean button */}
        <button
          onClick={handleClean}
          disabled={!input.trim()}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 
                     text-white disabled:text-gray-500 dark:disabled:text-gray-400 rounded-lg font-medium text-sm 
                     transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                     dark:focus:ring-offset-gray-900"
        >
          Clean Claude Text
        </button>

        {/* Results section */}
        {result && (
          <div className="space-y-3 pt-1 border-t border-gray-200 dark:border-gray-800">
            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-2.5">
                <p className="text-xs text-yellow-700 dark:text-yellow-300 font-medium mb-0.5">
                  Note
                </p>
                <ul className="text-xs text-yellow-600 dark:text-yellow-400 space-y-0.5">
                  {result.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Stats */}
            <div className="flex gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span>
                Before: {result.stats.originalWords.toLocaleString()} words
              </span>
              <span>
                After: {result.stats.transformedWords.toLocaleString()} words
              </span>
              <span>{result.stats.sentences} sentences</span>
            </div>

            {/* Comparison */}
            <Comparison
              original={result.original}
              transformed={result.transformed}
            />

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="flex-1 py-2 px-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
                           text-gray-800 dark:text-gray-200 rounded-lg text-sm font-medium transition-colors
                           focus:outline-none focus:ring-2 focus:ring-gray-400"
              >
                {copied ? 'Copied!' : 'Copy Clean Text'}
              </button>
              <button
                onClick={handleClear}
                className="py-2 px-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
                           text-gray-500 dark:text-gray-400 rounded-lg text-sm transition-colors
                           focus:outline-none focus:ring-2 focus:ring-gray-400"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 dark:text-gray-500 leading-relaxed pt-1">
          This transformation changes the statistical properties of the text, but
          cannot guarantee that Claude's watermark detection will no longer
          identify it. All processing is done locally in your browser — nothing is
          uploaded.
        </p>
      </main>

      {/* Settings modal */}
      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  )
}