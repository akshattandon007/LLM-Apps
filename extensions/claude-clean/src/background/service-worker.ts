/**
 * Claude Clean — Background Service Worker
 *
 * Adds a context menu item on claude.ai for right-click → Clean with Claude Clean.
 * Stores selected text in chrome.storage so the popup can pick it up on open.
 */

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'claude-clean-selection',
    title: 'Clean with Claude Clean',
    contexts: ['selection'],
    documentUrlPatterns: ['https://claude.ai/*'],
  })
})

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === 'claude-clean-selection' && info.selectionText) {
    chrome.storage.local.set({ incomingText: info.selectionText })
  }
})

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === 'getIncomingText') {
    chrome.storage.local.get('incomingText', (result) => {
      const text = result.incomingText || ''
      if (text) chrome.storage.local.remove('incomingText')
      sendResponse({ text })
    })
    return true
  }
})

export {}