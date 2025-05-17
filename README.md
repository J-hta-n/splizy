# Python environment

- Switch to python 3.10.1, then create a virtual environment, activate it, then install depedencies

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

# Pre-commit hook

- If pre-commit is not yet installed run `pip install pre-commit`
- Run `pre-commit run --all` before every commit

# Running Splizy

- To serve webhook locally, first obtain WEBHOOK_URL by running `ngrok http <PORT>` and copying the public domain given by ngrok to your local env file, then start the server with `python3 main.py` on a separate terminal which sets the webhook upon bot instantiation
- To serve webhook publicly, Koyeb was used to deploy the server on a public WEBHOOK_URL, which was then reconfigured in Koyeb secrets. Only after the first deployment would the webhook need to be manually set by running

```bash
  curl -X POST "https://api.telegram.org/bot<TELEBOT_TOKEN>/setWebhook" \
   -d url=WEBHOOK_URL \
   -d secret_token=SECRET_TOKEN
```

- Subsequently, as long as WEBHOOK_URL doesn't change, future deployments will set the correct webhook automatically
