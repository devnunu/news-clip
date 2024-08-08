import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import requests
import json

WEBHOOK_URL = "your_slack_webhook_url"

class SlackNotifier:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL
        self.username = "깐추리"
        self.avatar_url = "https://example.com/avatar.png"  # 아바타 이미지 URL

    def send_message(self, message, username="Bot", avatar_url=None):
        payload = {
            "text": message,
            "username": username,  # 사용자 이름 설정
        }

        if avatar_url:
            payload["icon_url"] = avatar_url  # 아바타 이미지 설정

        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            raise ValueError(
                f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")