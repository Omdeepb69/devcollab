import logging
from typing import Dict, List, Optional
from github import Github, GithubException

logger = logging.getLogger(__name__)

class GitHubIntegration:
    def __init__(self, token: str):
        """
        Initialize GitHub integration with the provided token.
        
        Args:
            token (str): GitHub Personal Access Token
        """
        self.github = Github(token)
        self.user = self.github.get_user()
    
    def get_repositories(self, include_private: bool = False) -> List[Dict]:
        """
        Get repositories for the authenticated user.
        
        Args:
            include_private (bool): Whether to include private repositories
            
        Returns:
            list: List of repository information
        """
        try:
            repos = []
            for repo in self.user.get_repos():
                if include_private or not repo.private:
                    repos.append({
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "url": repo.html_url,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "language": repo.language,
                        "private": repo.private,
                        "created_at": repo.created_at.isoformat(),
                        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
                    })
            return repos
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return []
    
    def get_collaborators(self, repo_name: str) -> List[Dict]:
        """
        Get collaborators for a repository.
        
        Args:
            repo_name (str): Repository name
            
        Returns:
            list: List of collaborator information
        """
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            collaborators = []
            
            for collaborator in repo.get_collaborators():
                collaborators.append({
                    "login": collaborator.login,
                    "name": collaborator.name,
                    "email": collaborator.email,
                    "avatar_url": collaborator.avatar_url,
                    "url": collaborator.html_url
                })
            
            return collaborators
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return []
    
    def create_issue(self, 
                    repo_name: str, 
                    title: str, 
                    body: str, 
                    assignees: Optional[List[str]] = None, 
                    labels: Optional[List[str]] = None) -> Dict:
        """
        Create an issue in a repository.
        
        Args:
            repo_name (str): Repository name
            title (str): Issue title
            body (str): Issue description
            assignees (list, optional): List of assignees
            labels (list, optional): List of labels
            
        Returns:
            dict: Issue information or error details
        """
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            
            # Create the issue
            issue = repo.create_issue(
                title=title,
                body=body,
                assignees=assignees or [],
                labels=labels or []
            )
            
            return {
                "status": "success",
                "issue": {
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None
                }
            }
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to create issue: {str(e)}"
            }
    
    def get_recent_commits(self, repo_name: str, count: int = 5) -> List[Dict]:
        """
        Get recent commits for a repository.
        
        Args:
            repo_name (str): Repository name
            count (int): Number of commits to retrieve
            
        Returns:
            list: List of commit information
        """
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            commits = []
            
            for commit in repo.get_commits()[:count]:
                commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                    "url": commit.html_url
                })
            
            return commits
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return []
    
    def create_webhook(self, 
                      repo_name: str, 
                      url: str, 
                      secret: Optional[str] = None, 
                      events: Optional[List[str]] = None) -> Dict:
        """
        Create a webhook for a repository.
        
        Args:
            repo_name (str): Repository name
            url (str): Webhook URL
            secret (str, optional): Webhook secret
            events (list, optional): List of events to trigger the webhook
            
        Returns:
            dict: Webhook information or error details
        """
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            
            # Set default events if not provided
            if not events:
                events = ["push", "pull_request"]
            
            # Create webhook config
            config = {
                "url": url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
            
            if secret:
                config["secret"] = secret
            
            # Create the webhook
            hook = repo.create_hook(
                name="web",
                config=config,
                events=events,
                active=True
            )
            
            return {
                "status": "success",
                "webhook": {
                    "id": hook.id,
                    "url": hook.config["url"],
                    "events": hook.events
                }
            }
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to create webhook: {str(e)}"
            }