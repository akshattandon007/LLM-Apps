// Service worker: when the toolbar icon is clicked on a tab that has our
// content script, ask it to toggle the chat panel. The popup.html handles
// non-content-scriptable pages (chrome:// etc.).

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.id) return;
  try {
    await chrome.tabs.sendMessage(tab.id, { type: "SKETCHIT_TOGGLE" });
  } catch (e) {
    // Content script not loaded (e.g. chrome:// pages); nothing to do.
    console.log("SketchIt: cannot toggle on this page", e);
  }
});
