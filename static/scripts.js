document.addEventListener("DOMContentLoaded", async function () {
  try {
    // Fetch the voice count from the backend (assuming the count is available)
    const response = await fetch("/voices/count");
    console.log("response");
    if (response.ok) {
      const { voiceCount } = await response.json();

      console.log(voiceCount);
      const voiceSelect = document.getElementById("voice");

      // Clear any existing options
      voiceSelect.innerHTML = "";

      // Populate the dropdown with available number of voices
      for (let i = 1; i <= voiceCount; i++) {
        const option = document.createElement("option");
        option.value = `${i}`;
        option.textContent = `${i}`;
        voiceSelect.appendChild(option);
      }
    } else {
      console.log("Failed to load voice count");
    }
  } catch (error) {
    console.log("Error loading voice count:", error);
  }
});

document
  .getElementById("messageForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById("message").value;
    const selectedVoice = document.getElementById("voice").value;
    console.log(selectedVoice)

    // Prepare the payload with the message and selected voice
    const payload = {
      message: message,
      voice: selectedVoice,
    };

    try {
      // Send the message with selected voice to the server
      const response = await fetch("/send-message", {
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
