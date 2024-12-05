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

document.addEventListener('DOMContentLoaded', function() {
  fetchStream("boo");
  console.log("DOMContentLoaded");
});

let sock;

let client_name = window.location.pathname.split('/').pop();
console.log(client_name);
let url = `ws://localhost:8122/ws/${client_name}`;

try {
  sock = new WebSocket(url);
  sock.onopen = function () {
    // send connect event
    console.log("onopen");
    sock.send(JSON.stringify({ event: 'connect', data: { client_id: client_name, client_type: 'frontend' } }));
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
} catch (err) {
  console.error('Error getting/displaying clients:', err);
}