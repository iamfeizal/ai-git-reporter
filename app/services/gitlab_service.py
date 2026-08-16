import requests

class GitLabService:
    def get_commits(self, url: str, token: str, project_id: str, start_date: str, end_date: str):
        api_url = f"{url}/api/v4/projects/{project_id}/repository/commits"
        headers = {"PRIVATE-TOKEN": token}
        params = {
            "since": f"{start_date}T00:00:00Z",
            "until": f"{end_date}T23:59:59Z",
            "with_stats": "true",
            "per_page": 100,
            "all": "true"
        }
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"GitLab API Error: {response.status_code} - {response.text}")