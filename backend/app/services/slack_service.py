"""
Slack Service
Handles all Slack Web API operations
"""

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.config import settings


class SlackService:
    """Service for interacting with Slack Web API"""
    
    def __init__(self):
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make a request to Slack API"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{endpoint}"
            if method == "GET":
                response = await client.get(url, headers=self.headers, params=data)
            else:
                response = await client.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
    
    async def get_channels(self) -> List[Dict]:
        """Get list of available Slack channels"""
        result = await self._make_request("GET", "conversations.list", {
            "types": "public_channel,private_channel",
            "exclude_archived": True,
            "limit": 100
        })
        return result.get("channels", [])
    
    async def get_users(self) -> List[Dict]:
        """Get list of Slack users"""
        result = await self._make_request("GET", "users.list")
        return result.get("members", [])
    
    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ) -> Dict:
        """Send a message to a Slack channel"""
        data = {
            "channel": channel,
            "text": text
        }
        if blocks:
            data["blocks"] = blocks
        
        return await self._make_request("POST", "chat.postMessage", data)
    
    async def send_standup_notification(
        self,
        channel_id: str,
        team_name: str,
        scheduled_time: datetime,
        jitsi_url: str,
        participants: List[Dict],
        issues: List[Dict]
    ) -> Dict:
        """Send standup notification with rich formatting"""
        
        # Format participants as mentions
        participant_mentions = " ".join([f"<@{p.get('slack_id', p.get('name'))}>" for p in participants])
        
        # Format issues list
        issues_text = "\n".join([
            f"• {issue.get('identifier', 'N/A')}: {issue.get('title', 'Untitled')}"
            for issue in issues[:10]  # Limit to 10 issues
        ])
        
        time_str = scheduled_time.strftime("%I:%M %p")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 Daily Standup Starting Now!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Team:*\n{team_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{time_str}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Join here:* <{jitsi_url}|Click to join Jitsi meeting>"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Participants:*\n{participant_mentions}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues to discuss ({len(issues)}):*\n{issues_text}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🎥 Join Meeting",
                            "emoji": True
                        },
                        "url": jitsi_url,
                        "style": "primary"
                    }
                ]
            }
        ]
        
        return await self.send_message(
            channel_id,
            f"Daily standup for {team_name} starting now! Join: {jitsi_url}",
            blocks
        )
    
    async def send_pm_summary(
        self,
        user_id: str,
        team_name: str,
        standup_date: datetime,
        progress_issues: List[Dict],
        blocked_issues: List[Dict],
        at_risk_issues: List[Dict],
        escalations: List[Dict]
    ) -> Dict:
        """Send PM summary via DM"""
        
        date_str = standup_date.strftime("%B %d, %Y")
        
        # Build progress section
        progress_text = "\n".join([
            f"• {issue.get('identifier')}: {issue.get('title')}"
            for issue in progress_issues
        ]) if progress_issues else "No issues in progress"
        
        # Build blocked section
        blocked_text = "\n".join([
            f"• {issue.get('identifier')}: {issue.get('title')} - {issue.get('blockers', 'Unknown blocker')}"
            for issue in blocked_issues
        ]) if blocked_issues else "No blocked issues"
        
        # Build at-risk section
        at_risk_text = "\n".join([
            f"• {issue.get('identifier')}: {issue.get('title')}"
            for issue in at_risk_issues
        ]) if at_risk_issues else "No at-risk issues"
        
        # Build escalations section
        escalations_text = "\n".join([
            f"• {esc.get('new_ticket_id')}: Created for {esc.get('original_issue_id')}"
            for esc in escalations
        ]) if escalations else "No escalations created"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Standup Summary - {team_name}",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {date_str}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*✅ Progress ({len(progress_issues)} issues):*\n{progress_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔴 Blocked ({len(blocked_issues)} issues):*\n{blocked_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ At Risk ({len(at_risk_issues)} issues):*\n{at_risk_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 Escalations Created ({len(escalations)}):*\n{escalations_text}"
                }
            }
        ]
        
        # Open DM channel with user
        dm_result = await self._make_request("POST", "conversations.open", {
            "users": user_id
        })
        
        if dm_result.get("ok"):
            channel_id = dm_result.get("channel", {}).get("id")
            return await self.send_message(
                channel_id,
                f"Standup summary for {team_name} on {date_str}",
                blocks
            )
        
        return dm_result


# Singleton instance
slack_service = SlackService()
