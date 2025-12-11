"""
Reasoning Service
Handles LLM-based extraction and analysis using OpenAI/Anthropic
"""

import httpx
import json
from typing import Dict, Optional, Any
from app.config import settings


class ReasoningService:
    """Service for LLM-based reasoning and extraction"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY
    
    async def _call_openai(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    
    async def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic Claude API using Claude Haiku 4.5"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-5-haiku-latest",
                    "max_tokens": 2048,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
    
    async def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """Call the configured LLM provider"""
        import logging
        logger = logging.getLogger("reasoning")
        
        if self.provider == "anthropic" and self.anthropic_key:
            logger.info("[Reasoning] Using Anthropic Claude API")
            return await self._call_anthropic(prompt, system_prompt)
        elif self.provider == "openai" and self.openai_key:
            logger.info("[Reasoning] Using OpenAI API")
            return await self._call_openai(prompt, system_prompt)
        elif self.anthropic_key:
            # Fallback to Anthropic if available
            logger.info("[Reasoning] Falling back to Anthropic API")
            return await self._call_anthropic(prompt, system_prompt)
        elif self.openai_key:
            # Fallback to OpenAI if available
            logger.info("[Reasoning] Falling back to OpenAI API")
            return await self._call_openai(prompt, system_prompt)
        else:
            # No API keys configured - return user-friendly message
            logger.warning("[Reasoning] No LLM API keys configured! Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")
            raise ValueError("No LLM API key configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file.")
    
    async def extract_update_from_transcript(
        self,
        transcript: str,
        issue_id: str,
        issue_title: str,
        assignee_name: str
    ) -> Dict:
        """Extract structured update from developer's verbal response"""
        
        system_prompt = """You are an AI assistant that extracts structured information from standup meeting transcripts.
        
You must extract the following information and return it as valid JSON:
- status: One of "progressing", "blocked", "completed", "at_risk"
- blockers: Any blockers mentioned (string or null)
- dependencies: Any dependencies on other teams/tasks (string or null)
- eta: Estimated completion date/time (string or null)
- next_steps: What the developer plans to do next (string or null)
- escalation_needed: Boolean - true if urgent attention needed
- escalation_reason: If escalation needed, explain why (string or null)

Return ONLY valid JSON, no other text."""

        prompt = f"""Issue: {issue_id} - {issue_title}
Assignee: {assignee_name}

Developer's update transcript:
"{transcript}"

Extract the structured information from this update."""

        try:
            response = await self._call_llm(prompt, system_prompt)
            
            # Parse JSON response
            # Clean up response if needed
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response.strip())
        except Exception as e:
            print(f"Error extracting update: {e}")
            return {
                "status": "progressing",
                "blockers": None,
                "dependencies": None,
                "eta": None,
                "next_steps": None,
                "escalation_needed": False,
                "escalation_reason": None
            }
    
    async def generate_standup_summary(
        self,
        issue_updates: list[Dict],
        team_name: str
    ) -> str:
        """Generate a comprehensive PM summary from all issue updates"""
        
        system_prompt = """You are an AI assistant that generates executive summaries for standup meetings.
        
Generate a clear, concise summary that highlights:
1. Overall team progress
2. Blocked items requiring attention
3. At-risk items
4. Escalations created
5. Key action items

Format the summary in a professional, easy-to-read manner."""

        issues_text = "\n".join([
            f"- {u.get('issue_id')}: {u.get('issue_title')} | Status: {u.get('status')} | Blockers: {u.get('blockers', 'None')} | ETA: {u.get('eta', 'Not specified')}"
            for u in issue_updates
        ])
        
        prompt = f"""Team: {team_name}

Issue Updates:
{issues_text}

Generate an executive summary for the PM."""

        try:
            return await self._call_llm(prompt, system_prompt)
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Standup completed for {team_name}. Please review individual issue updates for details."
    
    async def generate_linear_comment(
        self,
        status: str,
        blockers: Optional[str],
        dependencies: Optional[str],
        eta: Optional[str],
        next_steps: Optional[str],
        escalation_needed: bool,
        escalation_reason: Optional[str]
    ) -> str:
        """Generate formatted Linear comment from extracted data"""
        
        status_emoji = {
            "progressing": "🟢",
            "blocked": "🔴",
            "completed": "✅",
            "at_risk": "⚠️"
        }.get(status, "⚪")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
        
        comment_parts = [
            f"🤖 **Standup Update** - {timestamp}",
            "",
            f"**Status:** {status.title()} {status_emoji}"
        ]
        
        if blockers:
            comment_parts.append(f"**Blockers:** {blockers}")
        
        if dependencies:
            comment_parts.append(f"**Dependencies:** {dependencies}")
        
        if eta:
            comment_parts.append(f"**ETA:** {eta}")
        
        if next_steps:
            comment_parts.append(f"**Next Steps:** {next_steps}")
        
        if escalation_needed:
            comment_parts.extend([
                "",
                f"⚠️ **Escalation Required:** {escalation_reason}"
            ])
        
        return "\n".join(comment_parts)


# Singleton instance
reasoning_service = ReasoningService()
