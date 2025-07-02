
import os
import logging
from github import Github, GithubIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GithubService:
    def __init__(self, github_app_id: str, github_private_key: str):
        self.integration = GithubIntegration(github_app_id, github_private_key)

    def get_installation_url(self):
        return f"https://github.com/apps/commitz-installer/installations/new"

    def get_access_token(self, installation_id: int):
        return self.integration.get_access_token(installation_id)

    def get_github_instance(self, installation_id: int):
        access_token_info = self.get_access_token(installation_id)
        token = access_token_info.token
        return Github(token)

    def create_issue(self, installation_id: int, repo_name: str, title: str, body: str):
        g = self.get_github_instance(installation_id)
        try:
            repo = g.get_repo(repo_name)
            repo.create_issue(title=title, body=body)
            logger.info(f"Issue '{title}' created in repo '{repo_name}'")
        except Exception as e:
            logger.error(f"Failed to create issue in repo '{repo_name}': {e}")
            raise
