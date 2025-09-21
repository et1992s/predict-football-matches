# github_uploader.py
import base64
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubUploader:
    def __init__(self, token=None, repo_owner=None, repo_name=None, file_path="processed/today_matches.json", branch="master"):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo_owner = repo_owner or os.getenv('GITHUB_OWNER')
        self.repo_name = repo_name or os.getenv('GITHUB_REPO')
        self.file_path = file_path
        self.branch = branch

        if not all([self.token, self.repo_owner, self.repo_name]):
            raise ValueError("Missing GitHub configuration. Set GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")

        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{self.file_path}"

    def upload_to_github(self, data):
        """Upload JSON data to GitHub"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Check if file exists
            response = requests.get(self.api_url, headers=headers, params={"ref": self.branch})
            sha = response.json().get("sha") if response.status_code == 200 else None

            payload = {
                "message": f"📊 Update matches - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": base64.b64encode(json_data.encode("utf-8")).decode("utf-8"),
                "branch": self.branch,
                "sha": sha
            }

            response = requests.put(self.api_url, headers=headers, json=payload)
            response.raise_for_status()

            print(f"✅ Upload successful to GitHub!")
            print(f"📁 File: {self.file_path}")
            print(f"🔗 Raw URL: https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{self.file_path}")
            return True

        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False