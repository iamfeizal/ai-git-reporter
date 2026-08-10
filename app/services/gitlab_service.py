import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GitLabService:
    def __init__(self):
        self.token = os.getenv("GITLAB_TOKEN")
        self.base_url = os.getenv("GITLAB_URL")
        self.project_id = os.getenv("GITLAB_PROJECT_ID")
        self.headers = {"PRIVATE-TOKEN": self.token}

    def get_commits(self, start_date: str, end_date: str):
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/repository/commits"
        params = {
            "since": f"{start_date}T00:00:00Z",
            "until": f"{end_date}T23:59:59Z",
            "with_stats": "true",
            "per_page": 100,
            "all": "true"
        }
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"GitLab API Error: {response.status_code} - {response.text}")