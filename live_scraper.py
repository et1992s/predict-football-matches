import base64
import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# Citește din env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")


class GitHubUploader:
        # Folosește variabile de mediu sau parametri
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo_owner = repo_owner or os.getenv('GITHUB_OWNER')
        self.repo_name = repo_name or os.getenv('GITHUB_REPO')
        self.file_path = file_path

        if not all([self.token, self.repo_owner, self.repo_name]):
            raise ValueError(
                "Missing GitHub configuration. Set GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO environment variables.")

        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{self.file_path}"

    def upload_to_github(self, data):
        """Upload JSON data to GitHub"""
        try:
            # Converteste datele la JSON
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            # Headers pentru autentificare
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Verifică dacă fișierul există deja
            response = requests.get(self.api_url, headers=headers)
            sha = None
            if response.status_code == 200:
                sha = response.json().get('sha')

            # Prepare payload
            payload = {
                "message": f"📊 Update live matches - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": base64.b64encode(json_data.encode('utf-8')).decode('utf-8'),
                "sha": sha
            }

            # Upload
            response = requests.put(self.api_url, headers=headers, json=payload)
            response.raise_for_status()

            print(f"✅ Upload successful to GitHub!")
            print(f"📁 File: {self.file_path}")
            print(f"🔗 URL: https://github.com/{self.repo_owner}/{self.repo_name}/blob/main/{self.file_path}")

            return True

        except requests.exceptions.HTTPError as e:
            print(f"❌ GitHub API Error: {e}")
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False