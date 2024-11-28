let socket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;
const reconnectDelayBase = 1000;

let availableVoicesList = [];

// Connect to WebSocket
function connectToWebSocket() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    return;
  }

  socket = new WebSocket("ws://127.0.0.1:8000/ws");

  socket.onopen = function () {
    reconnectAttempts = 0;

    // Request the available voices from content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { type: "getVoices" });
    });
  };

  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);

    // Check for message and voice data
    if (data.message && data.voice) {
      // Send message to content script to speak the text
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
          chrome.tabs.sendMessage(tabs[0].id, {
            type: "speak",
            text: data.message,
            voice: data.voice,
          });
        }
      });
    }
  };

  socket.onclose = function () {
    attemptReconnect();
  };

  socket.onerror = function () {
    attemptReconnect();
  };
}

// Attempt to reconnect with exponential backoff
function attemptReconnect() {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++;
    const delay = reconnectDelayBase * Math.pow(2, reconnectAttempts);
    setTimeout(connectToWebSocket, delay);
  }
}

// Close WebSocket when tab becomes inactive
chrome.tabs.onActivated.addListener(function (activeInfo) {
  chrome.tabs.get(activeInfo.tabId, function (tab) {
    if (tab.status === "complete") {
      connectToWebSocket();
    }
  });
});

// Close WebSocket when tab is deactivated or goes into background
chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
  if (changeInfo.status === "loading") {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  }
});

// Connect to WebSocket when the extension is installed
chrome.runtime.onInstalled.addListener(function () {
  connectToWebSocket();
});

// Listen for voices data from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "voices") {
    // Store voices count instead of full voice data
    availableVoicesList = message.voices;

    // Send the number of voices to the server
    sendVoiceCountToServer(message.voices.length);
  }
});

// Function to send the number of voices to the server via WebSocket
function sendVoiceCountToServer(voiceCount) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(
      JSON.stringify({
        type: "available_voices_count",
        voiceCount: voiceCount,
      })
    );
  }
}
