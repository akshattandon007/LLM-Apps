/**
 * Local text transformation engine for Claude Clean.
 *
 * Pipeline:
 *   Original text → Sentence segmentation → Vocabulary variation →
 *   Sentence restructuring → Semantic consistency check → Transformed text
 *
 * Preserves: factual meaning, numbers, names, URLs, tone, structure.
 * Changes: sentence-level phrasing, word choices, clause ordering.
 *
 * Note: This changes the statistical properties of the text. It cannot
 * guarantee that Claude's watermark detection will no longer identify it.
 */

// ─── Synonym Bank ───────────────────────────────────────────────────────────

const SYNONYMS: Record<string, string[]> = {
  important: ['significant', 'crucial', 'critical', 'essential', 'key'],
  however: ['nevertheless', 'nonetheless', 'that said', 'yet', 'but then'],
  therefore: ['thus', 'consequently', 'as a result', 'hence', 'accordingly'],
  'for example': ['for instance', 'such as', 'to illustrate', 'e.g.'],
  show: ['demonstrate', 'illustrate', 'indicate', 'reveal', 'suggest', 'display'],
  make: ['create', 'form', 'generate', 'produce', 'build'],
  change: ['modify', 'alter', 'adjust', 'transform', 'revise', 'shift'],
  help: ['assist', 'aid', 'support', 'facilitate', 'enable'],
  provide: ['offer', 'supply', 'deliver', 'give', 'furnish'],
  need: ['require', 'necessitate', 'demand', 'call for'],
  way: ['method', 'approach', 'means', 'technique', 'strategy'],
  part: ['component', 'element', 'portion', 'segment', 'piece'],
  result: ['outcome', 'consequence', 'effect', 'impact', 'finding'],
  specific: ['particular', 'certain', 'distinct', 'definite', 'explicit'],
  different: ['distinct', 'various', 'diverse', 'contrasting'],
  allow: ['enable', 'permit', 'let', 'facilitate'],
  consider: ['examine', 'evaluate', 'assess', 'review', 'explore'],
  develop: ['create', 'build', 'form', 'establish', 'craft'],
  possible: ['feasible', 'achievable', 'attainable', 'viable', 'realistic'],
  likely: ['probable', 'plausible', 'expected', 'anticipated'],
  often: ['frequently', 'commonly', 'regularly', 'typically'],
  very: ['extremely', 'remarkably', 'notably', 'particularly', 'quite'],
  many: ['numerous', 'various', 'countless', 'multiple'],
  better: ['improved', 'superior', 'enhanced', 'stronger'],
  people: ['individuals', 'persons', 'users', 'professionals'],
  think: ['believe', 'consider', 'reckon', 'view', 'see'],
  know: ['understand', 'recognize', 'comprehend', 'realize'],
  good: ['excellent', 'great', 'fine', 'quality', 'positive'],
  big: ['large', 'substantial', 'considerable', 'significant', 'major'],
  new: ['fresh', 'novel', 'recent', 'modern', 'emerging'],
  first: ['initial', 'primary', 'foremost', 'principal', 'opening'],
  last: ['final', 'ultimate', 'concluding', 'terminal'],
  always: ['consistently', 'constantly', 'invariably', 'every time'],
  never: ['not once', 'under no circumstances', 'at no time'],
  must: ['should', 'ought to', 'need to', 'have to', 'is required to'],
  can: ['may', 'might', 'could', 'is able to', 'has the ability to'],
  because: ['since', 'as', 'given that', 'due to the fact that'],
  about: ['regarding', 'concerning', 'pertaining to', 'with respect to'],
  also: ['additionally', 'furthermore', 'moreover', 'besides'],
  so: ['thus', 'hence', 'accordingly', 'consequently'],
  then: ['subsequently', 'afterward', 'later', 'following that'],
  now: ['currently', 'presently', 'at this point', 'nowadays'],
  like: ['similar to', 'akin to', 'comparable to', 'resembling'],
  just: ['merely', 'simply', 'only', 'exactly'],
  actually: ['in fact', 'in reality', 'indeed', 'as a matter of fact'],
  generally: ['typically', 'broadly', 'commonly', 'usually'],
  usually: ['ordinarily', 'typically', 'generally', 'normally'],
  especially: ['particularly', 'notably', 'specially', 'above all'],
  potentially: ['possibly', 'conceivably', 'in principle'],
  ultimately: ['eventually', 'finally', 'in the end', 'after all'],
  currently: ['at present', 'presently', 'now', 'as of now'],
  previously: ['formerly', 'earlier', 'prior to this', 'in the past'],
  main: ['primary', 'principal', 'chief', 'central', 'key'],
  simple: ['straightforward', 'uncomplicated', 'basic', 'easy'],
  complex: ['complicated', 'intricate', 'sophisticated', 'elaborate'],
  clear: ['evident', 'apparent', 'obvious', 'transparent'],
  correct: ['accurate', 'proper', 'right', 'precise', 'valid'],
  quick: ['rapid', 'fast', 'swift', 'prompt', 'speedy'],
  significant: ['substantial', 'considerable', 'marked', 'notable'],
  entire: ['whole', 'complete', 'full', 'total', 'thorough'],
  various: ['diverse', 'assorted', 'different', 'sundry'],
  numerous: ['countless', 'multiple', 'abundant', 'plentiful'],
  several: ['multiple', 'a few', 'a number of', 'various'],
  useful: ['helpful', 'valuable', 'beneficial', 'practical'],
  appropriate: ['suitable', 'fitting', 'proper', 'relevant'],
  necessary: ['required', 'essential', 'needed', 'vital'],
}

// ─── Utility ────────────────────────────────────────────────────────────────

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

// ─── Sentence Segmentation ──────────────────────────────────────────────────

function splitSentences(text: string): string[] {
  // Simple regex-based sentence splitting
  const raw = text.match(/[^.!?\n]+[.!?]*(\n|$)/g) || [text]
  return raw.map((s) => s.trim()).filter(Boolean)
}

// ─── Vocabulary Variation ───────────────────────────────────────────────────

function varyVocabulary(sentence: string): string {
  let result = sentence
  const words = Object.keys(SYNONYMS).sort((a, b) => b.length - a.length) // longer first to avoid partial matches

  for (const word of words) {
    // Match word as a whole word (case-insensitive)
    const regex = new RegExp(`\\b${escapeRegex(word)}\\b`, 'gi')
    if (regex.test(result)) {
      const synonyms = SYNONYMS[word]
      // Don't replace every occurrence — target ~40-60% of them
      result = result.replace(regex, (match) => {
        if (Math.random() < 0.5) return match // keep original half the time
        const replacement = pick(synonyms)
        // Preserve capitalization
        if (match[0] === match[0].toUpperCase()) {
          return replacement.charAt(0).toUpperCase() + replacement.slice(1)
        }
        return replacement
      })
    }
  }

  return result
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// ─── Sentence Restructuring ────────────────────────────────────────────────

/**
 * Simple restructure rules:
 * 1. If sentence starts with "Despite", move the clause around.
 * 2. If sentence has "because", try flipping the order.
 * 3. If sentence is long (3+ clauses), ~30% chance to split into two sentences.
 */
function restructureSentence(sentence: string): string {
  const s = sentence.trim()

  // Rule 1: Despite X, Y → Y, despite X
  const despiteMatch = s.match(/^Despite\s+(.+?),\s*(.+)/i)
  if (despiteMatch && Math.random() < 0.5) {
    return `${despiteMatch[2]}, despite ${despiteMatch[1].toLowerCase()}`
  }

  // Rule 2: X because Y → Because Y, X
  const becauseMatch = s.match(/^(.+?)\s+because\s+(.+)/i)
  if (becauseMatch && Math.random() < 0.5) {
    return `Because ${becauseMatch[2]}, ${becauseMatch[1].toLowerCase()}`
  }

  // Rule 3: X because Y, Z → Y, so X, Z (when cause is first)
  const causeMatch = s.match(/^(.+?),\s+because\s+(.+?),\s+(.+)/i)
  if (causeMatch && Math.random() < 0.4) {
    return `${causeMatch[2]}, so ${causeMatch[1].toLowerCase()}, ${causeMatch[3]}`
  }

  // Rule 4: Although/While X, Y → Y, although/while X
  const concessiveMatch = s.match(/^(Although|While)\s+(.+?),\s*(.+)/i)
  if (concessiveMatch && Math.random() < 0.5) {
    const conj = concessiveMatch[1].toLowerCase()
    return `${concessiveMatch[3]}, ${conj} ${concessiveMatch[2].toLowerCase()}`
  }

  // Rule 5: Long sentence with two commas — ~25% chance to split
  if (s.split(',').length >= 3 && Math.random() < 0.25) {
    const commaIdx = s.indexOf(',')
    if (commaIdx > 0 && commaIdx < s.length - 1) {
      const first = s.slice(0, commaIdx).trim()
      const rest = s.slice(commaIdx + 1).trim()
      return `${first}. ${rest.charAt(0).toUpperCase() + rest.slice(1)}`
    }
  }

  return s
}

// ─── Semantic Consistency Check ────────────────────────────────────────────

/**
 * Basic fact-preservation check.
 * Verifies that all numbers, URLs, and named entities (words with capitals
 * that aren't at the start of a sentence) are preserved.
 * Returns warnings but always returns the transformed text.
 */
function checkConsistency(original: string, transformed: string): {
  text: string
  warnings: string[]
} {
  const warnings: string[] = []

  // Extract numbers (integers and decimals)
  const origNumbers: string[] = original.match(/\b\d+(?:\.\d+)?/g) || []
  const transNumbers: string[] = transformed.match(/\b\d+(?:\.\d+)?/g) || []
  for (const num of origNumbers) {
    if (!transNumbers.includes(num)) {
      warnings.push(`Number "${num}" may have been dropped.`)
    }
  }

  // Extract URLs
  const urlRegex = /https?:\/\/[^\s]+/g
  const origUrls: string[] = original.match(urlRegex) || []
  const transUrls: string[] = transformed.match(urlRegex) || []
  for (const url of origUrls) {
    if (!transUrls.includes(url)) {
      warnings.push(`URL "${url}" may have been dropped.`)
    }
  }

  // Extract capitalized proper nouns (not at start of sentence)
  const properNounRegex = /\b[A-Z][a-z]{2,}\b/g
  const origNouns = [...new Set<string>(original.match(properNounRegex) || [])]
  const transNouns = [...new Set<string>(transformed.match(properNounRegex) || [])]
  for (const noun of origNouns) {
    // Skip if it's just the first word of a sentence in original
    const firstWord = original.match(/^[A-Z][a-z]+/)
    if (firstWord && firstWord[0] === noun) continue

    if (!transNouns.includes(noun)) {
      warnings.push(`Name "${noun}" may have been altered.`)
    }
  }

  return { text: transformed, warnings }
}

// ─── Main Transformation Pipeline ──────────────────────────────────────────

export interface TransformResult {
  original: string
  transformed: string
  warnings: string[]
  stats: {
    originalWords: number
    transformedWords: number
    sentences: number
  }
}

function wordCount(text: string): number {
  return text.split(/\s+/).filter(Boolean).length
}

export function transformText(original: string): TransformResult {
  if (!original.trim()) {
    return {
      original: '',
      transformed: '',
      warnings: [],
      stats: { originalWords: 0, transformedWords: 0, sentences: 0 },
    }
  }

  // 1. Sentence segmentation
  const sentences = splitSentences(original)

  // 2. Vocabulary variation + sentence restructuring per sentence
  const transformedSentences = sentences.map((sentence) => {
    let result = varyVocabulary(sentence)
    result = restructureSentence(result)
    return result
  })

  // 3. Join
  const transformed = transformedSentences.join(' ')

  // 4. Semantic consistency check
  const { text: finalText, warnings } = checkConsistency(original, transformed)

  return {
    original,
    transformed: finalText,
    warnings,
    stats: {
      originalWords: wordCount(original),
      transformedWords: wordCount(finalText),
      sentences: sentences.length,
    },
  }
}

/**
 * Seed the RNG for deterministic testing (pass a number).
 * In production, we use Math.random() which is fine for this use case.
 */
export function seedRng(seed: number): void {
  // Simple seeded random — not cryptographic, just for consistent transforms
  let s = seed
  // Override Math.random with a simple LCG
  const originalRandom = Math.random
  Math.random = (): number => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
  // Store original for restoration
  ;(Math as any).__originalRandom = originalRandom
}

export function restoreRng(): void {
  if ((Math as any).__originalRandom) {
    Math.random = (Math as any).__originalRandom
    delete (Math as any).__originalRandom
  }
}