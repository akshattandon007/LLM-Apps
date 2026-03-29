chrome.commands.onCommand.addListener((command) => {
  if (command === "toggle-palette") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]?.id) return;
      const tabId = tabs[0].id;
      chrome.tabs.sendMessage(tabId, { action: "toggle-palette" }, (response) => {
        if (chrome.runtime.lastError) {
          // Content script not yet injected — inject it now
          chrome.scripting.executeScript({
            target: { tabId },
            files: ["templates.js", "content.js"]
          }).then(() => {
            chrome.scripting.insertCSS({ target: { tabId }, files: ["styles.css"] });
            // Give it a moment to initialize, then send the toggle
            setTimeout(() => {
              chrome.tabs.sendMessage(tabId, { action: "toggle-palette" });
            }, 200);
          }).catch(() => {});
        }
      });
    });
  }
});

chrome.action.onClicked.addListener((tab) => {
  if (!tab.id) return;
  chrome.tabs.sendMessage(tab.id, { action: "toggle-palette" }, (response) => {
    if (chrome.runtime.lastError) {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["templates.js", "content.js"]
      }).then(() => {
        chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ["styles.css"] });
        setTimeout(() => {
          chrome.tabs.sendMessage(tab.id, { action: "toggle-palette" });
        }, 200);
      }).catch(() => {});
    }
  });
});
