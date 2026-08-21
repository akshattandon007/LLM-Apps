/**
 * Claude Clean — Content Script for claude.ai
 *
 * Adds a small "Clean with Claude Clean" button next to Claude's output
 * text areas so users can select text and trigger cleaning without leaving
 * the page.
 *
 * Also adds a context menu item via the background worker for right-click
 * cleaning.
 */

import { transformText } from '../transform/local-transform'

// ─── UI Injection ───────────────────────────────────────────────────────────

const BUTTON_ID = 'claude-clean-btn'
const TOAST_ID = 'claude-clean-toast'

function injectCleanButton(targetElement: HTMLElement) {
  if (targetElement.querySelector(`#${BUTTON_ID}`)) return

  const btn = document.createElement('button')
  btn.id = BUTTON_ID
  btn.textContent = 'Clean with Claude Clean'
  btn.style.cssText = `
    position: absolute;
    bottom: 8px;
    right: 8px;
    z-index: 9999;
    background: #4F46E5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    cursor: pointer;
    opacity: 0.9;
    transition: opacity 0.2s;
  `
  btn.addEventListener('mouseenter', () => { btn.style.opacity = '1' })
  btn.addEventListener('mouseleave', () => { btn.style.opacity = '0.9' })

  btn.addEventListener('click', () => {
    // Try to find text content near the button
    const parent = targetElement.closest('[class*="font-claude"]') ||
                   targetElement.closest('[class*="message"]') ||
                   targetElement.closest('[class*="conversation-turn"]')
    const textEl = parent?.querySelector('[class*="font-claude"]') ||
                   parent?.querySelector('[class*="whitespace-pre-wrap"]')

    let text = ''
    if (textEl?.textContent) {
      text = textEl.textContent
    } else {
      // Fallback: try the clicking target's parent text content
      text = targetElement.textContent || ''
    }

    if (text.trim()) {
      const result = transformText(text)
      // Show toast with result
      showToast(result.transformed)
    }
  })

  targetElement.style.position = 'relative'
  targetElement.appendChild(btn)
}

function showToast(text: string) {
  const existing = document.getElementById(TOAST_ID)
  if (existing) existing.remove()

  const toast = document.createElement('div')
  toast.id = TOAST_ID
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 99999;
    max-width: 380px;
    max-height: 300px;
    overflow-y: auto;
    background: #1F2937;
    color: #F3F4F6;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.5;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  `

  // Copy button in toast
  const copyBtn = document.createElement('button')
  copyBtn.textContent = 'Copy'
  copyBtn.style.cssText = `
    background: #4F46E5;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    cursor: pointer;
    margin-bottom: 8px;
  `
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(text)
    copyBtn.textContent = 'Copied!'
    setTimeout(() => copyBtn.remove(), 1500)
  })

  const closeBtn = document.createElement('button')
  closeBtn.innerHTML = '&times;'
  closeBtn.style.cssText = `
    background: transparent;
    color: #9CA3AF;
    border: none;
    font-size: 18px;
    cursor: pointer;
    float: right;
    line-height: 1;
  `
  closeBtn.addEventListener('click', () => toast.remove())

  const title = document.createElement('div')
  title.textContent = 'Claude Clean'
  title.style.cssText = `
    font-weight: 600;
    color: #818CF8;
    margin-bottom: 6px;
  `

  const body = document.createElement('div')
  body.textContent = text

  toast.appendChild(closeBtn)
  toast.appendChild(title)
  toast.appendChild(copyBtn)
  toast.appendChild(body)
  document.body.appendChild(toast)

  // Auto-dismiss after 30 seconds
  setTimeout(() => {
    if (document.getElementById(TOAST_ID)) {
      document.getElementById(TOAST_ID)?.remove()
    }
  }, 30000)
}

// ─── Observe DOM for Claude output elements ───────────────────────────────

function observeClaudeOutputs() {
  const observer = new MutationObserver(() => {
    // Look for selectable text areas in Claude's output
    const textBlocks = document.querySelectorAll(
      '[class*="font-claude"], [class*="whitespace-pre-wrap"], [class*="prose"]',
    )

    textBlocks.forEach((el) => {
      if (el instanceof HTMLElement && !el.querySelector(`#${BUTTON_ID}`)) {
        // Only inject on actual message content, not on tiny snippets
        const text = el.textContent || ''
        if (text.length > 80) {
          injectCleanButton(el)
        }
      }
    })
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  })
}

// ─── Init ───────────────────────────────────────────────────────────────────

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', observeClaudeOutputs)
} else {
  observeClaudeOutputs()
}

export {} // module boundary