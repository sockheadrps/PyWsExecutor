var image = document.getElementById('streamedImage'); // Ensure you have an image element with id 'streamedImage'

console.log('stream.js loaded');
let sock;
// Function to fetch the list of clients
async function getClients() {
  return fetch('/streamingWs')
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      return data.client_websockets;
    });
}

// Function to handle client stream selection
async function changeStream(clientId) {
  fetchStream(clientId); // Update the stream when the client is selected
}

// Wait until the DOM is fully loaded
document.addEventListener('DOMContentLoaded', async function () {
  let clientsContainer = document.getElementById('clients');
  let keypresses = document.getElementById('keypresses');

  if (!clientsContainer) {
    console.error('Could not find clients container element');
    return;
  }

  try {
    // Get the client names and display them as buttons
    let client_names = await getClients();
    if (!client_names) {
      console.error('No client names returned');
      return;
    }

    console.log('Client names:', client_names);
    for (let client_name of client_names) {
      let client = document.createElement('button');
      client.innerHTML = client_name;
      client.addEventListener('click', function () {
        // hide keyboard
        document.getElementById('keyboard').style.display = 'none';
        changeStream(client_name); // Update the stream when the client is selected
      });
      clientsContainer.appendChild(client);
      sock = new WebSocket('ws://localhost:8123/ws');

      sock.onopen = function () {
        // send connect event
        sock.send(JSON.stringify({ event: 'connect', data: { client_id: client_name, client_type: 'client_data' } }));
      };
      sock.onmessage = function (event) {
        console.log('message', event);
        let keypress = JSON.parse(event.data);
        if (keypress.event === 'keypress') {
          switch (keypress.data.key) {
            case 'backspace':
              // remove last character
              keypresses.innerHTML = keypresses.innerHTML.slice(0, -1);
              break;
            case 'space':
              keypresses.innerHTML += ' ';
              break;
            default:
              keypresses.innerHTML += keypress.data.key;
              break;
          }
        }
      };
    }
  } catch (err) {
    console.error('Error getting/displaying clients:', err);
  }
});


async function fetchStream(client_id) {
  const response = await fetch(`/stream/${client_id}`);
  const reader = response.body.getReader();
  let buffer = new Uint8Array();

  const boundary = new TextEncoder().encode('--frame');
  const delimiter = new TextEncoder().encode('\r\n\r\n');

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // Append new data to the buffer
    const tempBuffer = new Uint8Array(buffer.length + value.length);
    tempBuffer.set(buffer);
    tempBuffer.set(value, buffer.length);
    buffer = tempBuffer;

    let boundaryIndex = findSubarray(buffer, boundary);
    while (boundaryIndex !== -1) {
      const nextBoundaryIndex = findSubarray(
        buffer,
        boundary,
        boundaryIndex + boundary.length
      );
      if (nextBoundaryIndex === -1) break;

      const frameData = buffer.slice(
        boundaryIndex + boundary.length,
        nextBoundaryIndex
      );
      const headerEndIndex = findSubarray(frameData, delimiter);
      if (headerEndIndex !== -1) {
        const headers = new TextDecoder().decode(
          frameData.slice(0, headerEndIndex)
        );
        const body = frameData.slice(
          headerEndIndex + delimiter.length
        );

        // Create and display the image
        const blob = new Blob([body], { type: 'image/webp' });
        const imgElement = document.getElementById('streamedImage');
        if (imgElement) {
          imgElement.src = URL.createObjectURL(blob);
        }
        
      }

      boundaryIndex = nextBoundaryIndex;
    }

    // Trim buffer to exclude processed data
    if (boundaryIndex === -1) {
      buffer = buffer.slice(boundaryIndex);
    }
  }
}

// Utility function to find subarray index
function findSubarray(buffer, subarray, start = 0) {
  for (let i = start; i <= buffer.length - subarray.length; i++) {
    let match = true;
    for (let j = 0; j < subarray.length; j++) {
      if (buffer[i + j] !== subarray[j]) {
        match = false;
        break;
      }
    }
    if (match) return i;
  }
  return -1;
}

if (sock) {
  sock.onmessage = function (event) {
    console.log('message', event);
  };
}
