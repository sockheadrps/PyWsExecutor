let availableVoices = [];

// Function to handle when voices change (loaded after page load)
function onVoicesChanged() {
  availableVoices = speechSynthesis.getVoices();

  if (availableVoices.length === 0) {
    console.error("No voices available.");
    return;
  }

  sendVoicesToBackground(availableVoices);
}

// Function to send voices to the background script
function sendVoicesToBackground(voices) {
  chrome.runtime.sendMessage({
    type: "voices",
    voices: voices,
  });
}

if ("speechSynthesis" in window) {
  // If voices are already available, use them immediately
  if (speechSynthesis.getVoices().length === 0) {
    speechSynthesis.onvoiceschanged = onVoicesChanged;
  } else {
    // Voices are already loaded, call onVoicesChanged to send them to the background script
    availableVoices = speechSynthesis.getVoices();
    onVoicesChanged();
  }
} else {
  console.error("Speech synthesis is not supported in this browser.");
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "getVoices") {
    let voices = speechSynthesis.getVoices();
    if (voices.length === 0) {
      speechSynthesis.onvoiceschanged = function () {
        voices = speechSynthesis.getVoices();
        sendResponse(voices);
        sendVoicesToBackground(voices);
      };
    } else {
      sendResponse(voices);
      sendVoicesToBackground(voices);
    }
    return true; 
  } else if (message.type === "speak") {
    if (typeof SpeechSynthesisUtterance !== "undefined") {
      const utterance = new SpeechSynthesisUtterance(message.text);
      const voices = speechSynthesis.getVoices();
      utterance.voice = voices[message.voice];
      speechSynthesis.speak(utterance);
    }
  }
});

// Listen for page visibility changes (when the page is cached or goes to background)
document.addEventListener("visibilitychange", function () {
  if (document.hidden) {
    console.log("Page is hidden. Pausing TTS or performing necessary cleanup.");
  } else {
    console.log("Page is visible again.");
  }
});
