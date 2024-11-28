document
  .getElementById("messageForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById("message").value;

    // Prepare the payload with the message and selected voice
    const payload = {
      message: message,
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
