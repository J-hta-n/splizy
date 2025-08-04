# Splizy

@splizy_bot is a telegram bot which helps members in group chats consolidate and split bills more conveniently without using any 3rd party apps.

# Python environment

- Switch to python 3.12, create a virtual environment, activate it, then install depedencies

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

- Alternatively, containerise with Docker:

```bash
docker build -t splizy-bot .
```

# Pre-commit hook

- If pre-commit is not yet installed run `pip install pre-commit`
- Run `pre-commit run --all` before every commit

# Running Splizy

- Obtain a telegram bot token via @BotFather and place it in local .env file, then run:
  - if using venv:
    `python3 main.py`
  - if using Docker:
    `docker run --rm --env-file .env splizy-bot`
