document.addEventListener("DOMContentLoaded", function () {
  const keys = document.querySelectorAll(".key"); // All the keys
  const pressedKeysDisplay = document.getElementById("pressedKeys"); // Display pressed keys
  const sendKeysButton = document.getElementById("sendKeysButton"); // Send keys button
  const pressedKeys = []; // Array to track pressed keys (regular keys)
  const comboToggleButton = document.getElementById("comboToggleButton"); // Combo toggle button
  const clearPressedKeysBtn = document.getElementById("clearPressedKeysBtn"); // Clear button
  const addDelayButton = document.getElementById("addDelayButton"); // Delay button
  const delayInput = document.getElementById("delayInput"); // Delay input field
  const wordInput = document.getElementById("wordInput"); // Word input field
  const addWordButton = document.getElementById("addWordButton"); // Word button

  let comboState = "press";
  let comboKeys = { hold: [], press: [] };

  keys.forEach((key) => {
    key.addEventListener("click", function () {
      const keyValue = key.textContent.trim();

      if (comboState === "press") {
        pressedKeys.push({ press: keyValue });
      } else if (comboState === "combo") {
        comboKeys.hold.push(keyValue);
      } else if (comboState === "finish") {
        comboKeys.press.push(keyValue);
      }

      updatePressedKeysDisplay();
      toggleSendButton();
    });
  });

  addWordButton.addEventListener("click", function () {
    const wordValue = wordInput.value.trim();
    if (wordValue) {
      pressedKeys.push({ word: wordValue });
      wordInput.value = "";
      updatePressedKeysDisplay();
      toggleSendButton();
    } else {
      alert("Please enter a valid word.");
    }
  });

  comboToggleButton.addEventListener("click", function () {
    if (comboState === "press") {
      comboState = "combo";
      comboToggleButton.textContent = "Combo Press";
    } else if (comboState === "combo") {
      comboState = "finish";
      comboToggleButton.textContent = "Finish Combo";
    } else if (comboState === "finish") {
      comboState = "press";
      comboToggleButton.textContent = "Combo Mode";
      pressedKeys.push({
        combo: { hold: [...comboKeys.hold], press: [...comboKeys.press] },
      });
      comboKeys = { hold: [], press: [] };
    }

    updatePressedKeysDisplay();
  });

  clearPressedKeysBtn.addEventListener("click", function () {
    if (
      pressedKeys.length === 0 &&
      comboKeys.hold.length === 0 &&
      comboKeys.press.length === 0
    ) {
      console.log("No keys to clear.");
      return;
    }

    if (comboKeys.press.length > 0 || comboKeys.hold.length > 0) {
      comboKeys = { hold: [], press: [] };
    } else {
      pressedKeys.pop();
    }

    updatePressedKeysDisplay();
    toggleSendButton();
  });

  addDelayButton.addEventListener("click", function () {
    const delayValue = parseFloat(delayInput.value);
    if (isNaN(delayValue) || delayValue <= 0) {
      alert("Please enter a valid delay time greater than 0.");
      return;
    }

    pressedKeys.push({ delay: delayValue.toString() });
    delayInput.value = "";
    updatePressedKeysDisplay();
    toggleSendButton();
  });

  function updatePressedKeysDisplay() {
    let displayText = "";

    // Regular pressed keys
    if (pressedKeys.length > 0) {
      displayText = pressedKeys
        .map((key) =>
          key.press
            ? key.press
            : key.word
            ? `Word: ${key.word}`
            : key.delay
            ? `Delay: ${key.delay}s`
            : `Combo: Hold [${key.combo.hold.join(
                ", "
              )}], Press [${key.combo.press.join(", ")}]`
        )
        .join(", ");
    }

    if (comboState === "combo") {
      displayText += ` (Combo Mode: Hold - [${comboKeys.hold.join(", ")}])`;
    } else if (comboState === "finish") {
      displayText += ` (Combo Mode: Hold - [${comboKeys.hold.join(
        ", "
      )}], Press - [${comboKeys.press.join(", ")}])`;
    }

    if (displayText === "") {
      pressedKeysDisplay.textContent = "No keys pressed yet.";
    } else {
      pressedKeysDisplay.textContent = displayText;
    }
  }

  function toggleSendButton() {
    if (
      pressedKeys.length === 0 &&
      comboKeys.hold.length === 0 &&
      comboKeys.press.length === 0
    ) {
      sendKeysButton.disabled = true;
    } else {
      sendKeysButton.disabled = false;
    }
  }

  function sendComboKeys() {
    const payload = {
      event: "keypress",
      data: { keys: [...pressedKeys] },
    };

    try {
      console.log(payload);

      fetch("/send-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Keys sent successfully: " + data.status);
        })
        .catch((error) => {
          console.log("Error sending keys:", error);
        });

      clearAll();
      updatePressedKeysDisplay();
    } catch (error) {
      console.log("Error sending combo keys:", error);
    }
  }

  sendKeysButton.addEventListener("click", function () {
    sendComboKeys();
  });

  function clearAll() {
    pressedKeys.length = 0;
    comboKeys = { hold: [], press: [] };
    comboState = "press";
    comboToggleButton.textContent = "Combo Hold";
  }

  // Handle form submission for sending the message and volume
  document
    .getElementById("messageForm")
    .addEventListener("submit", async function (event) {
      event.preventDefault();

      const message = document.getElementById("message").value;
      const volume = document.getElementById("volume").value;

      const payload = {
        event: "tts",
        data: {
          message: message,
          volume: volume,
        },
      };

      try {
        console.log(payload);

        const response = await fetch("/send-event", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          const data = await response.json();
          console.log("Message sent successfully: " + data.status);
        } else {
          console.log("Failed to send message");
        }
      } catch (error) {
        console.log("Error sending message:", error);
      }
    });

  document.getElementById("volume").addEventListener("input", function () {
    document.getElementById("volumeValue").textContent = this.value;
  });
});
