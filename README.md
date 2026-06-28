# DawClock2Vtuber

> MIDI clock to VTube Studio head animation — your avatar nods along while you produce.

Make your VTube Studio avatar nod to your DAW's beat.

When you hit play in your DAW, your avatar starts bobbing its head in sync with the tempo. Hit stop, it settles back to idle. Works by reading MIDI clock and pushing head parameters into VTube Studio over the API.

## What it does

- Nods on every beat (FaceAngleY / pitch)
- Light sway and roll on accented beats so it doesn't look stiff
- Eyes blink a bit while nodding
- Optional Y-axis bob for extra motion
- All spring-damper physics — no hard snaps, everything decays naturally
- Tiny random jitter so the avatar doesn't look frozen between beats
- GUI panel with sliders to tweak everything live, no restart needed
- Auto-reconnects if VTube Studio drops
- Saves the VTS auth token locally so you only click Allow once

## Setup

You need Windows (10 or 11), Python 3.9+, and VTube Studio.

### loopMIDI

This is how your DAW talks to the script. Grab [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html), run it, click + and name the port `DawClock2Vtube`.

### VTube Studio

Go to Settings, flip on "Allow Plugin API Access". Default port 8001 is fine.

### Install

```bash
git clone https://github.com/YOUR_USERNAME/DawClock2Vtuber.git
cd DawClock2Vtuber
pip install pygame websocket-client
python main.py
```

### DAW

In your DAW's MIDI settings, point MIDI clock output at `DawClock2Vtube`. Press play.

## The GUI

A small tkinter window pops up. Sliders for everything:

- **Nod intensity** — pitch angle on beat (default 5°)
- **Y bob** — up/down bounce, toggle + strength
- **Yaw sway** — tiny left/right on accents (keep this low, like 0.15°)
- **Roll** — head tilt on accents (0.1° default)
- **Decay** — how fast it settles back (0.8-0.88 is good)
- **Speed** — overall multiplier, 0.35 default. Turn it down if it feels twitchy
- **Blink** — eye close amount while nodding
- **Jitter** — human-like micro movement amount

Everything applies immediately. Closing the window just hides it, the program keeps going.

## config.py

```python
VTS_HOST = "127.0.0.1"
VTS_PORT = 8001
MIDI_PORT_NAME = "DawClock2Vtube"

NOD_INTENSITY = 5.0
ANIMATION_DECAY = 0.82
ANIMATION_SPEED = 0.35
SEND_RATE = 60
EYE_BLINK_STRENGTH = 0.35
```

Change defaults there if you want. GUI overrides whatever config says while running.

## Problems?

- **"No MIDI input ports found"** — loopMIDI isn't running or the port doesn't exist
- **"Cannot connect"** — VTS not open, or API not enabled in settings
- **"Click Allow"** — look at VTS, there's a permission dialog waiting
- **Avatar won't move** — double check your DAW is actually sending clock to the right port
- **Too fast / jittery** — lower the speed multiplier in the GUI
- **My model uses different axis names** — edit `beat_animation.py`, swap FaceAngleX/Y if needed

## Files

```
├── main.py           # entry point
├── config.py         # defaults live here
├── beat_animation.py # the physics engine
├── vts_client.py     # websocket stuff for VTS
├── midi_handler.py   # reads midi clock via pygame
├── gui.py            # tkinter control panel
└── vts_token.json    # auth token, auto-generated
```

made with GitHub Copilot

## License

MIT
