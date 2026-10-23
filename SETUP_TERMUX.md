# StromXDevs — Termux setup

## 1. Install Termux packages

```bash
pkg update
pkg install python python-pillow
```

## 2. Enter the bot folder

```bash
cd ~/storage/shared/Alarms/StromXDevs
```

If your folder is elsewhere, `cd` to the folder containing `main.py`.

## 3. Install Python packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This version intentionally does **not** install `openai`, `jiter`, `duckduckgo-search`, `numpy`, `psutil`, or `pyttsx3`, because they are not needed to start the bot and some cause Android/Termux build problems. AI uses the OpenAI-compatible HTTP API directly.

## 4. Set your bot token

Never paste the token into chat. In Termux:

```bash
export TOKEN='YOUR_NEW_BOT_TOKEN'
```

If the token was ever posted publicly, regenerate it in the Discord Developer Portal before using it.

## 5. Optional AI key

The default `config.yml` uses Groq's OpenAI-compatible endpoint. Set a valid key if you want the AI features:

```bash
export AI_API_KEY='YOUR_AI_API_KEY'
```

## 6. Start

```bash
python main.py
```

## 7. If you close Termux

The bot stops when the Termux process is stopped. This is not 24/7 hosting.


## StromXDevs emojis

The bot tries to load the application's custom emojis when it starts. If the app emojis cannot be fetched or used, `utils/stromx_emojis.py` returns Discord-native Unicode emoji instead, so emoji fields do not render as blank. Look for the startup line `StromXDevs emojis: X/Y custom loaded; native fallbacks enabled`.
