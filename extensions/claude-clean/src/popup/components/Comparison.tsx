interface ComparisonProps {
  original: string
  transformed: string
}

export default function Comparison({ original, transformed }: ComparisonProps) {
  if (!original && !transformed) return null

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-3">
        {/* Before */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
            Before
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-3 min-h-[80px] max-h-[200px] overflow-y-auto">
            <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
              {original || (
                <span className="italic text-gray-400 dark:text-gray-500">
                  Original text will appear here
                </span>
              )}
            </p>
          </div>
        </div>
        {/* After */}
        <div>
          <h3 className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-1">
            After
          </h3>
          <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 min-h-[80px] max-h-[200px] overflow-y-auto">
            <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
              {transformed || (
                <span className="italic text-gray-400 dark:text-gray-500">
                  Cleaned text will appear here
                </span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}