# WebSocket TTS Interface

This project is a WebSocket front-end interface, server, and remote client for sending keystrokes, or executing TTS remotely to the websocket client.

## Features

- **On-Screen Keyboard**: A fully interactive on-screen keyboard with keypress functionality.
- **Text-to-Speech (TTS)**: Ability to send text messages for TTS with configurable volume.
- **Customizable Settings**: Includes options to add delays between key presses, add words, and send keystrokes with or without combo hold.
- **Primarily directx compliant**: Games will recognize keystrokes.

## Screenshots

![Screenshot of the interface](giffy.gif)

## The webserver is meant to be hosted on a VPS, or otherwise made available to access over http

## The client is run on some target computer, and ideally set to run on startup.

![frontend](frontend.png)

### Keystroke execution JSON structure:

```
{
  "event": "keypress",
  "data": {
    "keys": [
      { "press": "A" },
      { "press": "B" },
      {
        "combo": {
          "hold": ["Ctrl"],
          "press": ["B"]
        }
      },
      { "delay": "0.5" },
      { "press": "C" }
    ]
  }
}
```

### TTS JSON structure:

```
{
  "event": "tts",
  "data": {
    "message": "hahaha",
    "volume": "1"
    }
}
```

Running with Windows task scheduler:

<details>
  <summary>Click to expand</summary>
  
```
hit win+r or super+r
```
and type

```
taskschd.msc
```
into the run prompt.


![into the run prompt.](assets/1.png)

Name the task, adjust these settings as you see fit.

![](assets/2.png)


Go to the settings tab to handle task lifecycle.

![](assets/3.png)


Go to actions tab, click new, and locate the installed version of python.
![](assets/4.png)

Use pythonw.exe for headless. Arguements will be where the python WS client is.

![](assets/5.png)

Finally head to triggers, dicate when the script should be triggered to start.

![](assets/6.png)


</details>


