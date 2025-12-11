"""
Linear Service
Handles all Linear API GraphQL operations
"""

import httpx
from typing import List, Optional, Dict, Any
from app.config import settings


class LinearService:
    """Service for interacting with Linear GraphQL API"""
    
    def __init__(self):
        self.api_url = settings.LINEAR_API_URL
        self.headers = {
            "Authorization": settings.LINEAR_API_KEY,
            "Content-Type": "application/json"
        }
    
    async def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against Linear API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={"query": query, "variables": variables or {}},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_teams(self) -> List[Dict]:
        """Fetch all teams from Linear"""
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        result = await self._execute_query(query)
        return result.get("data", {}).get("teams", {}).get("nodes", [])
    
    async def get_team_members(self, team_id: str) -> List[Dict]:
        """Fetch all members of a specific team"""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                members {
                    nodes {
                        id
                        name
                        email
                        avatarUrl
                    }
                }
            }
        }
        """
        result = await self._execute_query(query, {"teamId": team_id})
        return result.get("data", {}).get("team", {}).get("members", {}).get("nodes", [])
    
    async def get_team_issues(self, team_id: str, active_only: bool = True) -> List[Dict]:
        """Fetch issues for a team, optionally filtering for active issues only"""
        query = """
        query($teamId: String!, $filter: IssueFilter) {
            team(id: $teamId) {
                issues(filter: $filter) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        state {
                            id
                            name
                            type
                        }
                        assignee {
                            id
                            name
                            email
                        }
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        
        filter_var = None
        if active_only:
            filter_var = {
                "state": {
                    "type": {"nin": ["completed", "canceled"]}
                }
            }
        
        result = await self._execute_query(query, {
            "teamId": team_id,
            "filter": filter_var
        })
        return result.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
    
    async def get_issue(self, issue_id: str) -> Optional[Dict]:
        """Fetch a single issue by ID"""
        query = """
        query($issueId: String!) {
            issue(id: $issueId) {
                id
                identifier
                title
                description
                priority
                state {
                    id
                    name
                    type
                }
                assignee {
                    id
                    name
                    email
                }
                createdAt
                updatedAt
            }
        }
        """
        result = await self._execute_query(query, {"issueId": issue_id})
        return result.get("data", {}).get("issue")
    
    async def add_comment(self, issue_id: str, comment: str) -> Dict:
        """Add a comment to a Linear issue"""
        mutation = """
        mutation($issueId: String!, $body: String!) {
            commentCreate(input: {issueId: $issueId, body: $body}) {
                success
                comment {
                    id
                    body
                    createdAt
                }
            }
        }
        """
        result = await self._execute_query(mutation, {
            "issueId": issue_id,
            "body": comment
        })
        return result.get("data", {}).get("commentCreate", {})
    
    async def update_issue_status(self, issue_id: str, state_id: str) -> Dict:
        """Update the status/state of a Linear issue"""
        mutation = """
        mutation($issueId: String!, $stateId: String!) {
            issueUpdate(id: $issueId, input: {stateId: $stateId}) {
                success
                issue {
                    id
                    identifier
                    state {
                        id
                        name
                    }
                }
            }
        }
        """
        result = await self._execute_query(mutation, {
            "issueId": issue_id,
            "stateId": state_id
        })
        return result.get("data", {}).get("issueUpdate", {})
    
    async def create_escalation_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        parent_issue_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: int = 1,
        labels: List[str] = None
    ) -> Dict:
        """Create an escalation issue in Linear"""
        mutation = """
        mutation($teamId: String!, $title: String!, $description: String!, 
                 $parentId: String, $assigneeId: String, $priority: Int) {
            issueCreate(input: {
                teamId: $teamId,
                title: $title,
                description: $description,
                parentId: $parentId,
                assigneeId: $assigneeId,
                priority: $priority
            }) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        result = await self._execute_query(mutation, {
            "teamId": team_id,
            "title": title,
            "description": description,
            "parentId": parent_issue_id,
            "assigneeId": assignee_id,
            "priority": priority
        })
        return result.get("data", {}).get("issueCreate", {})
    
    async def get_workflow_states(self, team_id: str) -> List[Dict]:
        """Get all workflow states for a team"""
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                        color
                        position
                    }
                }
            }
        }
        """
        result = await self._execute_query(query, {"teamId": team_id})
        return result.get("data", {}).get("team", {}).get("states", {}).get("nodes", [])
    
    async def get_issue_by_identifier(self, identifier: str) -> Optional[Dict]:
        """Fetch an issue by its identifier (e.g., 'ENG-123')"""
        query = """
        query($filter: IssueFilter!) {
            issues(filter: $filter, first: 1) {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    estimate
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    team {
                        id
                        name
                    }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        # Parse identifier to get team key and number
        parts = identifier.split("-")
        if len(parts) != 2:
            return None
        
        team_key, number = parts
        try:
            num_val = int(number)
        except ValueError:
            return None
        
        result = await self._execute_query(query, {
            "filter": {
                "number": {"eq": num_val},
                "team": {"key": {"eq": team_key}}
            }
        })
        
        nodes = result.get("data", {}).get("issues", {}).get("nodes", [])
        return nodes[0] if nodes else None
    
    async def update_issue_estimate(self, issue_id: str, estimate_days: int) -> Dict:
        """Update the estimate (in points/days) for a Linear issue"""
        mutation = """
        mutation($issueId: String!, $estimate: Float!) {
            issueUpdate(id: $issueId, input: {estimate: $estimate}) {
                success
                issue {
                    id
                    identifier
                    estimate
                }
            }
        }
        """
        result = await self._execute_query(mutation, {
            "issueId": issue_id,
            "estimate": float(estimate_days)
        })
        return result.get("data", {}).get("issueUpdate", {})
    
    async def update_issue_assignee(self, issue_id: str, assignee_id: str) -> Dict:
        """Update the assignee of a Linear issue"""
        mutation = """
        mutation($issueId: String!, $assigneeId: String!) {
            issueUpdate(id: $issueId, input: {assigneeId: $assigneeId}) {
                success
                issue {
                    id
                    identifier
                    assignee {
                        id
                        name
                        email
                    }
                }
            }
        }
        """
        result = await self._execute_query(mutation, {
            "issueId": issue_id,
            "assigneeId": assignee_id
        })
        return result.get("data", {}).get("issueUpdate", {})


# Singleton instance
linear_service = LinearService()

