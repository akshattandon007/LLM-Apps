import { useRef, useEffect } from 'react'

interface TextEditorProps {
  value: string
  onChange: (value: string) => void
}

export default function TextEditor({ value, onChange }: TextEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 280)}px`
    }
  }, [value])

  const wordCount = value ? value.split(/\s+/).filter(Boolean).length : 0
  const charCount = value.length

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">
        Paste Claude-generated text here
      </label>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste Claude-generated text here..."
        className="w-full min-h-[120px] max-h-[280px] p-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-y
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   placeholder:text-gray-400 dark:placeholder:text-gray-500
                   focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                   text-sm leading-relaxed"
        spellCheck={false}
      />
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>
          {wordCount} word{wordCount !== 1 ? 's' : ''}
        </span>
        <span>
          {charCount.toLocaleString()} character{charCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  )
}