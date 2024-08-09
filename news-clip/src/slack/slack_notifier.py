import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import requests
import json

WEBHOOK_URL = "https://hooks.slack.com/services/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"

class SlackNotifier:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL

    def send_message(self, message):
        payload = {
            "text": message,  # 메시지 텍스트
        }

        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            raise ValueError(
                f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}"
            )