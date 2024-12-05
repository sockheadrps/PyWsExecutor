document.addEventListener('DOMContentLoaded', function () {
  const keys = document.querySelectorAll('.key'); // All the keys
  const pressedKeysDisplay = document.getElementById('pressedKeys'); // Display pressed keys
  const sendKeysButton = document.getElementById('sendKeysButton'); // Send keys button
  const pressedKeys = []; // Array to track pressed keys (regular keys)
  const comboToggleButton = document.getElementById(
    'comboToggleButton'
  ); // Combo toggle button
  const clearPressedKeysBtn = document.getElementById(
    'clearPressedKeysBtn'
  ); // Clear button
  const addDelayButton = document.getElementById('addDelayButton'); // Delay button
  const delayInput = document.getElementById('delayInput'); // Delay input field
  const wordInput = document.getElementById('wordInput'); // Word input field
  const addWordButton = document.getElementById('addWordButton'); // Word button

  const keyStatusTab = document.getElementById('keyStatusTab');
  const formTab = document.getElementById('formTab');
  const shortcutsTab = document.getElementById('shortcutsTab'); // New Shortcuts tab
  const keyStatusContent = document.getElementById(
    'keyStatusContent'
  );
  const formContent = document.getElementById('formContent');
  const shortcutsContent = document.getElementById(
    'shortcutsContent'
  ); // Shortcuts content section
  const shortcutsContainer = document.getElementById(
    'shortcutsContainer'
  ); // Shortcuts container

  // Activate Key Status tab by default
  keyStatusTab.classList.add('active');
  keyStatusContent.classList.add('active');

  let shortcuts = [
    {
      name: 'open-website',
      keys: [
        { press: 'winleft' },
        { word: 'opera' },
        { press: 'Enter' },
        { delay: '1' },
        { word: '' }, // Empty value
        { press: 'Enter' },
      ],
    },
    {
      name: 'close-window',
      keys: [{ combo: { hold: ['Ctrl'], press: ['f4'] } }],
    },
    {
      name: 'screenshot',
      keys: [],
    },
  ];

  shortcuts.forEach((shortcut) => {
    const shortcutElement = document.createElement('button');
    shortcutElement.classList.add('shortcut');
    shortcutElement.textContent = shortcut.name;
    shortcutsContainer.appendChild(shortcutElement);
  });

  document.querySelectorAll('.shortcut').forEach((shortcut) => {
    shortcut.addEventListener('click', function () {
      const shortcutName = this.textContent;
      const shortcutData = shortcuts.find(
        (s) => s.name === shortcutName
      );

      if (shortcutName === 'screenshot') {
        const payload = {
          event: 'screenshot',
          data: {},
        };

        try {
          console.log(payload);

          fetch('/send-event', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
          })
            .then((response) => response.json())
            .then((data) => {
              console.log('Keys sent successfully: ' + data.status);
            })
            .catch((error) => {
              console.log('Error sending keys:', error);
            });

          clearAll();
          updatePressedKeysDisplay();
        } catch (error) {
          console.log('Error sending combo keys:', error);
        }
        return;
      }

      // Hide shortcuts container
      shortcutsContainer.style.display = 'none';

      // Create shortcut view container
      const shortCutView = document.createElement('div');
      shortCutView.classList.add('shortcut-view');
      shortcutsContent.appendChild(shortCutView);

      if (shortcutData) {
        const jsonValuesContainer = document.createElement('div');
        jsonValuesContainer.classList.add('json-values-container');
        shortCutView.appendChild(jsonValuesContainer);

        shortcutData.keys.forEach((key, position) => {
          const keyValue = Object.values(key)[0];
          const keyName = Object.keys(key)[0];

          if (keyValue === '') {
            // Handle empty keys
            console.log('EMPTY KEY FOUND', key);
            console.log('Position is', position);

            // Input container for entering key sequences
            const inputContainer = document.createElement('div');
            inputContainer.classList.add('input-container');

            const keyTextBox = document.createElement('input');
            keyTextBox.placeholder = 'Enter sequence';

            const setButton = document.createElement('button');
            setButton.textContent = 'Set';

            // Set button functionality
            setButton.addEventListener('click', function () {
              const value = keyTextBox.value.trim();
              if (!value) {
                alert('Please enter a valid key sequence.');
                return;
              }

              // Update the shortcutData key
              shortcutData.keys[position][keyName] = value;
              console.log('Updated shortcutData:', shortcutData);

              // Update the button text in the UI
              const selectedButton =
                jsonValuesContainer.querySelector(
                  '.shortcut-key.selected'
                );
              if (selectedButton) {
                selectedButton.textContent = value;
              }

              // Clear the input box
              keyTextBox.value = '';
            });

            inputContainer.append(keyTextBox, setButton);
            shortCutView.appendChild(inputContainer);
          } else {
            // Display existing keys
            console.log('KEY FOUND', keyValue);
          }

          // Add button for each key
          const keyButton = document.createElement('button');
          keyButton.classList.add('shortcut-key');
          if (typeof keyValue == 'object') {
            keyButton.textContent = JSON.stringify(keyValue) || '';
          } else {
            keyButton.textContent = keyValue || '';
          }
          jsonValuesContainer.appendChild(keyButton);

          keyButton.addEventListener('click', function () {
            jsonValuesContainer
              .querySelectorAll('.shortcut-key')
              .forEach((btn) => btn.classList.remove('selected'));
            keyButton.classList.add('selected');
          });
        });

        // Add "Send" button
        const sendButton = document.createElement('button');
        sendButton.textContent = 'Send';
        shortCutView.appendChild(sendButton);

        sendButton.addEventListener('click', function () {
          const payload = {
            event: 'keypress',
            data: { keys: [...shortcutData.keys] },
          };
          console.log('Sending payload:', payload);

          fetch('/send-event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          })
            .then((response) => response.json())
            .then((data) => {
              console.log('Keys sent successfully:', data.status);
            })
            .catch((error) => {
              console.error('Error sending keys:', error);
            });
        });
      }
    });
  });

  // Tab switching functionality
  keyStatusTab.addEventListener('click', function () {
    keyStatusTab.classList.add('active');
    formTab.classList.remove('active');
    shortcutsTab.classList.remove('active'); // Deselect Shortcuts tab
    keyStatusContent.classList.add('active');
    formContent.classList.remove('active');
    shortcutsContent.classList.remove('active'); // Hide Shortcuts content
  });

  formTab.addEventListener('click', function () {
    formTab.classList.add('active');
    keyStatusTab.classList.remove('active');
    shortcutsTab.classList.remove('active'); // Deselect Shortcuts tab
    formContent.classList.add('active');
    keyStatusContent.classList.remove('active');
    shortcutsContent.classList.remove('active'); // Hide Shortcuts content
  });

  shortcutsTab.addEventListener('click', function () {
    shortcutsTab.classList.add('active');
    keyStatusTab.classList.remove('active');
    formTab.classList.remove('active');
    shortcutsContent.classList.add('active');
    keyStatusContent.classList.remove('active');
    formContent.classList.remove('active');
    shortcutsContainer.style.display = 'block';
  });

  let comboState = 'press';
  let comboKeys = { hold: [], press: [] };

  keys.forEach((key) => {
    key.addEventListener('click', function () {
      const keyValue = key.textContent.trim();

      if (comboState === 'press') {
        pressedKeys.push({ press: keyValue });
      } else if (comboState === 'combo') {
        comboKeys.hold.push(keyValue);
      } else if (comboState === 'finish') {
        comboKeys.press.push(keyValue);
      }

      updatePressedKeysDisplay();
      toggleSendButton();
    });
  });

  addWordButton.addEventListener('click', function () {
    const wordValue = wordInput.value.trim();
    if (wordValue) {
      pressedKeys.push({ word: wordValue });
      wordInput.value = '';
      updatePressedKeysDisplay();
      toggleSendButton();
    } else {
      alert('Please enter a valid word.');
    }
  });

  comboToggleButton.addEventListener('click', function () {
    if (comboState === 'press') {
      comboState = 'combo';
      comboToggleButton.textContent = 'Combo Press';
    } else if (comboState === 'combo') {
      comboState = 'finish';
      comboToggleButton.textContent = 'Finish Combo';
    } else if (comboState === 'finish') {
      comboState = 'press';
      comboToggleButton.textContent = 'Combo Mode';
      pressedKeys.push({
        combo: {
          hold: [...comboKeys.hold],
          press: [...comboKeys.press],
        },
      });
      comboKeys = { hold: [], press: [] };
    }

    updatePressedKeysDisplay();
  });

  clearPressedKeysBtn.addEventListener('click', function () {
    if (
      pressedKeys.length === 0 &&
      comboKeys.hold.length === 0 &&
      comboKeys.press.length === 0
    ) {
      console.log('No keys to clear.');
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

  addDelayButton.addEventListener('click', function () {
    const delayValue = parseFloat(delayInput.value);
    if (isNaN(delayValue) || delayValue <= 0) {
      alert('Please enter a valid delay time greater than 0.');
      return;
    }

    pressedKeys.push({ delay: delayValue.toString() });
    delayInput.value = '';
    updatePressedKeysDisplay();
    toggleSendButton();
  });

  function updatePressedKeysDisplay() {
    let displayText = '';

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
                ', '
              )}], Press [${key.combo.press.join(', ')}]`
        )
        .join(', ');
    }

    if (comboState === 'combo') {
      displayText += ` (Combo Mode: Hold - [${comboKeys.hold.join(
        ', '
      )}])`;
    } else if (comboState === 'finish') {
      displayText += ` (Combo Mode: Hold - [${comboKeys.hold.join(
        ', '
      )}], Press - [${comboKeys.press.join(', ')}])`;
    }

    if (displayText === '') {
      pressedKeysDisplay.textContent = 'No keys pressed yet.';
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
      event: 'keypress',
      data: { keys: [...pressedKeys] },
    };

    try {
      console.log(payload);

      fetch('/send-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log('Keys sent successfully: ' + data.status);
        })
        .catch((error) => {
          console.log('Error sending keys:', error);
        });

      clearAll();
      updatePressedKeysDisplay();
    } catch (error) {
      console.log('Error sending combo keys:', error);
    }
  }

  sendKeysButton.addEventListener('click', function () {
    sendComboKeys();
  });

  function clearAll() {
    pressedKeys.length = 0;
    comboKeys = { hold: [], press: [] };
    comboState = 'press';
    comboToggleButton.textContent = 'Combo Hold';
  }

  // Handle form submission for sending the message and volume
  document
    .getElementById('messageForm')
    .addEventListener('submit', async function (event) {
      event.preventDefault();

      const message = document.getElementById('message').value;
      const volume = document.getElementById('volume').value;

      const payload = {
        event: 'tts',
        data: {
          message: message,
          volume: volume,
        },
      };

      try {
        console.log(payload);

        const response = await fetch('/send-event', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Message sent successfully: ' + data.status);
        } else {
          console.log('Failed to send message');
        }
      } catch (error) {
        console.log('Error sending message:', error);
      }
    });

  document
    .getElementById('volume')
    .addEventListener('input', function () {
      document.getElementById('volumeValue').textContent = this.value;
    });
  var RangeSlider = (function () {
    var elRangeInputs = document.querySelectorAll('.range');

    function setProgress(elTarget) {
      var elRangeBar = elTarget.parentElement;
      var intThumbWidth = elRangeBar.clientHeight * 3;
      var intRangeBarWidth = elRangeBar.clientWidth - intThumbWidth;
      var intThumbWidthOffset = intThumbWidth / 2;

      var intProgressPosition =
        (elTarget.value - elTarget.min) /
        (elTarget.max - elTarget.min);
      var intRangePosition =
        intRangeBarWidth * intProgressPosition + intThumbWidthOffset;

      elRangeBar.style.background =
        'linear-gradient(to right, #423089 ' +
        intRangePosition +
        'px, #e2e2ea ' +
        intRangePosition +
        'px';
    }

    for (var i = 0; i < elRangeInputs.length; i++) {
      elRangeInputs[i].firstElementChild.addEventListener(
        'input',
        function () {
          setProgress(this);
        }
      );

      setProgress(elRangeInputs[i].firstElementChild);
    }
  })();
});

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
        changeStream(client_name); // Update the stream when the client is selected
        document.getElementById('keyboard-container').style.display =
          'flex';
        document.getElementById(
          'keyboard-container'
        ).style.flexDirection = 'row';
        document.getElementById('keyboard-container').style.margin =
          '10px';
        document.getElementById('keyboard-container').style.padding =
          '0px';
        document.getElementById(
          'keyboard-container'
        ).style.placeSelf = 'flex-end';
        document.getElementById(
          'keyboard-container'
        ).style.alignItems = 'center';

        // keyboard container
        document.getElementById('keyboard').style.width = '50%';
        document.getElementById('keyboard').style.height = '50%';
        document.getElementById('keyboard').style.margin = '0px';
        document.getElementById('keyboard').style.padding = '0px';

        document.querySelectorAll('key').style.width = '15px';
        document.querySelectorAll('key').style.height = '15px';
        document.querySelectorAll(
          'div-center-wrapper'
        ).style.padding = '0px';
        document.querySelectorAll('div-center-wrapper').style.width =
          '50%';
        document.getElementById('keyboard-container').style.margin = '20px';
      });
      clientsContainer.appendChild(client);
      sock = new WebSocket('ws://localhost:8123/ws');

      sock.onopen = function () {
        // send connect event
        sock.send(
          JSON.stringify({
            event: 'connect',
            data: {
              client_id: client_name,
              client_type: 'client_data',
            },
          })
        );
      };
      sock.onmessage = function (event) {
        console.log('message', event);
        let keypress = JSON.parse(event.data);
        if (keypress.event === 'keypress') {
          switch (keypress.data.key) {
            case 'backspace':
              // remove last character
              keypresses.innerHTML = keypresses.innerHTML.slice(
                0,
                -1
              );
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
