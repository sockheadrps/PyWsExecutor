document.addEventListener("DOMContentLoaded", function () {
  const keys = document.querySelectorAll(".key"); // All the keys
  const pressedKeysDisplay = document.getElementById("pressedKeys"); // Display pressed keys
  const sendKeysButton = document.getElementById("sendKeysButton"); // Send keys button
  const pressedKeys = new Set(); // To track pressed keys
  const volumeSlider = document.getElementById("volume"); // Volume slider

  // Highlight the key and add/remove it from pressed keys set
  keys.forEach((key) => {
    key.addEventListener("click", function () {
      const keyValue = key.textContent.trim(); // Get the key's value
      if (pressedKeys.has(keyValue)) {
        // If key is already pressed, remove it
        pressedKeys.delete(keyValue);
        key.classList.remove("highlight");
      } else {
        // If key is not pressed, add it
        pressedKeys.add(keyValue);
        key.classList.add("highlight");
      }
      updatePressedKeysDisplay(); // Update the pressed keys display
    });
  });

  // Update the displayed list of pressed keys
  function updatePressedKeysDisplay() {
    if (pressedKeys.size === 0) {
      pressedKeysDisplay.textContent = "No keys pressed yet.";
    } else {
      pressedKeysDisplay.textContent = Array.from(pressedKeys).join(", ");
    }
  }

  // Reset highlights and send keys when the send button is clicked
  sendKeysButton.addEventListener("click", async function () {
    // Prepare the payload with pressed keys and volume value
    const payload = {
      event: "keypress",  // Event type (you can choose any label you want for this event)
      data: {
        keys: Array.from(pressedKeys),  // The pressed keys as an array
      }
    };

    try {
      console.log(payload);  // For debugging

      // Send the event and data to the server via a POST request
      const response = await fetch("/send-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Keys sent successfully: " + data.status);
      } else {
        console.log("Failed to send keys");
      }

      // After sending, reset the highlighted keys
      keys.forEach((key) => key.classList.remove("highlight"));
      pressedKeys.clear();  // Clear the pressed keys set
      updatePressedKeysDisplay();  // Update the display after sending
    } catch (error) {
      console.log("Error sending keys:", error);
    }
  });

  // Handle form submission for sending the message and volume
  document.getElementById("messageForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById("message").value;
    const volume = document.getElementById("volume").value;  // Get the volume slider value

    // Prepare the payload with the message and volume values
    const payload = {
      event: "tts",  // Event type
      data: {
        message: message,  // The message entered
        volume: volume     // The volume value
      }
    };

    try {
      console.log(payload);  // For debugging

      // Send the event and data to the server via a POST request
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

  // Update the volume value dynamically as the slider changes
  document.getElementById("volume").addEventListener("input", function () {
    document.getElementById("volumeValue").textContent = this.value;
  });
});
