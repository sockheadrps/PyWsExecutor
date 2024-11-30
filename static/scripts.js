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

  const keyStatusTab = document.getElementById("keyStatusTab");
  const formTab = document.getElementById("formTab");
  const shortcutsTab = document.getElementById("shortcutsTab"); // New Shortcuts tab
  const keyStatusContent = document.getElementById("keyStatusContent");
  const formContent = document.getElementById("formContent");
  const shortcutsContent = document.getElementById("shortcutsContent"); // Shortcuts content section
  const shortcutsContainer = document.getElementById("shortcutsContainer"); // Shortcuts container

  // Activate Key Status tab by default
  keyStatusTab.classList.add("active");
  keyStatusContent.classList.add("active");

  let shortcuts = [
    {
      name: "open-website",
      keys: [
        { press: "winleft" },
        { word: "opera" },
        { press: "Enter" },
        { delay: "1" },
        { word: "" }, // Empty value
        { press: "Enter" },
      ],
    },
    {
      name: "close-tab",
      keys: [{ combo: { hold: ["Ctrl"], press: ["f4"] } }],
    },
    {
      name: "close-window",
      keys: [{ combo: { hold: ["Alt"], press: ["f4"] } }],
    },
  ];

  shortcuts.forEach((shortcut) => {
    const shortcutElement = document.createElement("button");
    shortcutElement.classList.add("shortcut");
    shortcutElement.textContent = shortcut.name;
    shortcutsContainer.appendChild(shortcutElement);
  });

  document.querySelectorAll(".shortcut").forEach((shortcut) => {
    shortcut.addEventListener("click", function () {
      // Hide shortcuts container
      shortcutsContainer.style.display = "none";

      // Create shortcut view container
      const shortCutView = document.createElement("div");
      shortCutView.classList.add("shortcut-view");
      shortcutsContent.appendChild(shortCutView);

      // Get shortcut data
      const shortcutName = this.textContent;
      const shortcutData = shortcuts.find((s) => s.name === shortcutName);
      console.log("Shortcut data:", shortcutData);
      console.log("Shortcut name:", shortcutName);

      if (shortcutData) {
        const jsonValuesContainer = document.createElement("div");
        jsonValuesContainer.classList.add("json-values-container");
        shortCutView.appendChild(jsonValuesContainer);

        shortcutData.keys.forEach((key, position) => {
          const keyValue = Object.values(key)[0];
          const keyName = Object.keys(key)[0];

          if (keyValue === "") {
            // Handle empty keys
            console.log("EMPTY KEY FOUND", key);
            console.log("Position is", position);

            // Input container for entering key sequences
            const inputContainer = document.createElement("div");
            inputContainer.classList.add("input-container");

            const keyTextBox = document.createElement("input");
            keyTextBox.placeholder = "Enter sequence";

            const setButton = document.createElement("button");
            setButton.textContent = "Set";

            // Set button functionality
            setButton.addEventListener("click", function () {
              const value = keyTextBox.value.trim();
              if (!value) {
                alert("Please enter a valid key sequence.");
                return;
              }

              // Update the shortcutData key
              shortcutData.keys[position][keyName] = value;
              console.log("Updated shortcutData:", shortcutData);

              // Update the button text in the UI
              const selectedButton = jsonValuesContainer.querySelector(
                ".shortcut-key.selected"
              );
              if (selectedButton) {
                selectedButton.textContent = value;
              }

              // Clear the input box
              keyTextBox.value = "";
            });

            inputContainer.append(keyTextBox, setButton);
            shortCutView.appendChild(inputContainer);
          } else {
            // Display existing keys
            console.log("KEY FOUND", keyValue);
          }

          // Add button for each key
          const keyButton = document.createElement("button");
          keyButton.classList.add("shortcut-key");
          if (typeof keyValue == "object") {
            keyButton.textContent = JSON.stringify(keyValue) || "";
          } else {
            keyButton.textContent = keyValue || "";
          }
          jsonValuesContainer.appendChild(keyButton);

          keyButton.addEventListener("click", function () {
            jsonValuesContainer
              .querySelectorAll(".shortcut-key")
              .forEach((btn) => btn.classList.remove("selected"));
            keyButton.classList.add("selected");
          });
        });

        // Add "Send" button
        const sendButton = document.createElement("button");
        sendButton.textContent = "Send";
        shortCutView.appendChild(sendButton);

        sendButton.addEventListener("click", function () {
          const payload = {
            event: "keypress",
            data: { keys: [...shortcutData.keys] },
          };
          console.log("Sending payload:", payload);

          fetch("/send-event", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          })
            .then((response) => response.json())
            .then((data) => {
              console.log("Keys sent successfully:", data.status);
            })
            .catch((error) => {
              console.error("Error sending keys:", error);
            });
        });
      }
    });
  });

  // Tab switching functionality
  keyStatusTab.addEventListener("click", function () {
    keyStatusTab.classList.add("active");
    formTab.classList.remove("active");
    shortcutsTab.classList.remove("active"); // Deselect Shortcuts tab
    keyStatusContent.classList.add("active");
    formContent.classList.remove("active");
    shortcutsContent.classList.remove("active"); // Hide Shortcuts content
  });

  formTab.addEventListener("click", function () {
    formTab.classList.add("active");
    keyStatusTab.classList.remove("active");
    shortcutsTab.classList.remove("active"); // Deselect Shortcuts tab
    formContent.classList.add("active");
    keyStatusContent.classList.remove("active");
    shortcutsContent.classList.remove("active"); // Hide Shortcuts content
  });

  shortcutsTab.addEventListener("click", function () {
    shortcutview = document.querySelector(".shortcut-view");
    const inputContainer = document.createElement("div");
    inputContainer.classList.add("input-container");

    const keyTextBox = document.createElement("input");
    keyTextBox.placeholder = "Enter sequence";

    const setButton = document.createElement("button");
    setButton.textContent = "Set";
    shortcutsTab.classList.add("active");
    keyStatusTab.classList.remove("active");
    formTab.classList.remove("active");
    shortcutsContent.classList.add("active");
    keyStatusContent.classList.remove("active");
    formContent.classList.remove("active");
  });

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
  var RangeSlider = (function () {
    var elRangeInputs = document.querySelectorAll(".range");

    function setProgress(elTarget) {
      var elRangeBar = elTarget.parentElement;
      var intThumbWidth = elRangeBar.clientHeight * 3;
      var intRangeBarWidth = elRangeBar.clientWidth - intThumbWidth;
      var intThumbWidthOffset = intThumbWidth / 2;

      var intProgressPosition =
        (elTarget.value - elTarget.min) / (elTarget.max - elTarget.min);
      var intRangePosition =
        intRangeBarWidth * intProgressPosition + intThumbWidthOffset;

      elRangeBar.style.background =
        "linear-gradient(to right, #423089 " +
        intRangePosition +
        "px, #e2e2ea " +
        intRangePosition +
        "px";
    }

    for (var i = 0; i < elRangeInputs.length; i++) {
      elRangeInputs[i].firstElementChild.addEventListener("input", function () {
        setProgress(this);
      });

      setProgress(elRangeInputs[i].firstElementChild);
    }
  })();
});
