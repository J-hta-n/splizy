# Splizy

@splizy_bot is a telegram bot which helps members in group chats consolidate and split bills more conveniently without using any 3rd party apps.

# Project Structure

```
├── src/
│   ├── bot/
│   │   ├── convo_handlers/     # Conversation flow handlers
│   │   │   ├── Base.py         # Base conversation handler to inherit from
│   │   │   └── ...
│   │   └── convo_utils/        # Conversation-specific utilities
│   │       └── ...
│   ├── utils/                  # General utilities
│   │   └── ...
│   └── telebot.py              # Main bot runner
├── config.py
├── main.py
├── Dockerfile
└── requirements.txt
```

# Running Splizy

## Python environment

- Switch to python 3.12, create a virtual environment, activate it, then install depedencies

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

- Alternatively, containerise with Docker:

```bash
docker build
```

- Obtain a telegram bot token via @BotFather and place it in local .env file, then run:

  - if using venv:
    `python3 main.py`
  - if using Docker:
    `docker run --rm --env-file .env splizy-bot`

## Lint / formatting: Pre-commit hook

- If pre-commit is not yet installed run `pip install pre-commit`
- Run `pre-commit run --all` before every commit
