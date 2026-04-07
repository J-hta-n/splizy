# Splizy

@splizy_bot is a telegram bot which helps members in group chats consolidate and split bills more conveniently without using any 3rd party apps.

# Project Structure

```
├── src/
│   ├── bot/
│   │   ├── convo_handlers/     # Conversation flow handlers
│   │   │   ├── Base.py         # Base conversation handler to inherit from
│   │   │   ├── <ConvoClass>/
│   │   │   │   ├── flows/      # Subconvos
│   │   │   │   ├── utils/      # Convo-specific utils
│   │   │   │   ├── context.py
│   │   │   │   ├── index.py
│   │   │   │   └── states.py
│   │   │   └── ...
│   │   ├── convo_utils/        # Global convo utils
│   │   └── telebot.py          # Main bot runner
│   └── lib/                    # External integrations and repos
│       └── receipt_parser/
│       └── splizy_repo/
├── receipt-miniapp/            # Next.js miniapp for receipt flow
│   ├── src/
│   │   ├── app/
│   │   │   ├── _components/    # Page specific components
│   │   │   ├── api/            # Data access layer
│   │   │   └── page.tsx
│   │   ├── components/         # Reusable components
│   │   └── lib/                # Configs and utils
│   └── package.json
├── config.py
├── main.py
├── Dockerfile
└── requirements.txt
```

# Running Splizy

## Quick start

1. Using python 3.12, create a virtual environment, activate it, then install depedencies

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

- Alternatively, containerise with Docker:

```bash
docker build
```

2. Create and configure your local .env with reference to .env.example, then run:

- if using venv:
  `python3 main.py`
- if using Docker:
  `docker run --rm --env-file .env splizy-bot`

## Receipt Parsing (Vision API)

- Currently uses Gemini's `gemini-2.5-flash-lite` model for receipt parsing
- Adjust `RECEIPT_PARSER_MONTHLY_LIMIT` to cap monthly usage

## Testing webhook locally

- When running server locally for development, polling telebot API is viable, but we can also simulate webhook hosting temporarily via a reverse proxy, eg using ngrok:

1. Run `ngrok http <PORT>` and copy the given public domain to `WEBHOOK_URL` in local .env
2. In a separate terminal, re-run splizy to set the webhook upon bot instantiation

## Lint / formatting: Pre-commit hook

- If pre-commit is not yet installed run `pip install pre-commit`
- Run `pre-commit run --all` before every commit
