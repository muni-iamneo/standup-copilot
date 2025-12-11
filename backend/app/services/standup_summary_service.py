"""
Standup Summary Service
Orchestrates post-call processing: extracts updates from transcripts,
updates Linear tickets, creates escalations, and posts to Slack
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from app.services.linear_service import linear_service
from app.services.slack_service import slack_service
from app.services.reasoning_service import reasoning_service

# Setup logger
logger = logging.getLogger("standup.summary")
logging.basicConfig(level=logging.INFO)


@dataclass
class IssueUpdate:
    """Structured update extracted for a Linear issue"""
    issue_identifier: str  # e.g., "ENG-123"
    issue_id: Optional[str] = None  # Linear UUID
    issue_title: Optional[str] = None
    status: str = "progressing"  # progressing, blocked, completed, at_risk
    blockers: Optional[str] = None
    dependencies: Optional[str] = None
    estimate_days: Optional[int] = None
    eta: Optional[str] = None
    next_steps: Optional[str] = None
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    new_assignee_email: Optional[str] = None
    transcript_snippet: Optional[str] = None


@dataclass
class SummaryResult:
    """Result of processing a standup session"""
    standup_id: str
    processed_at: datetime
    total_updates: int
    linear_comments_posted: int
    escalations_created: List[Dict]
    slack_posted: bool
    summary_text: str
    issue_updates: List[Dict]
    errors: List[str]


class StandupSummaryService:
    """Service to process standup session end and generate summaries"""
    
    async def process_session_end(
        self,
        standup_id: str,
        user_transcripts: List[Dict],
        agent_transcripts: List[Dict],
        team_id: str,
        slack_channel_id: str,
        issues_discussed: List[Dict] = None
    ) -> SummaryResult:
        """
        Main entry point: process end of standup session
        
        Args:
            standup_id: ID of the standup session
            user_transcripts: List of {text, timestamp} from user
            agent_transcripts: List of {text, timestamp} from AI agent
            team_id: Linear team ID for creating escalation tickets
            slack_channel_id: Slack channel to post summary
            issues_discussed: Optional list of issues that were discussed
        
        Returns:
            SummaryResult with all processing outcomes
        """
        logger.info(f"[Summary] Processing session end for standup {standup_id}")
        
        errors = []
        escalations_created = []
        linear_comments = 0
        
        # Step 1: Combine and format transcripts
        conversation = self._format_conversation(user_transcripts, agent_transcripts)
        logger.info(f"[Summary] Formatted conversation: {len(conversation)} characters")
        
        if not conversation or len(conversation) < 50:
            logger.info(f"[Summary] Conversation too short, skipping processing")
            return SummaryResult(
                standup_id=standup_id,
                processed_at=datetime.now(),
                total_updates=0,
                linear_comments_posted=0,
                escalations_created=[],
                slack_posted=False,
                summary_text="Conversation was too short to extract meaningful updates.",
                issue_updates=[],
                errors=["Conversation too short"]
            )
        
        # Step 2: Extract issue updates from conversation
        try:
            issue_updates = await self._extract_issue_updates(conversation, issues_discussed)
            logger.info(f"[Summary] Extracted {len(issue_updates)} issue updates")
        except Exception as e:
            logger.info(f"[Summary] Error extracting updates: {e}")
            errors.append(f"Extraction error: {str(e)}")
            issue_updates = []
        
        # Step 3: Apply updates to Linear
        for update in issue_updates:
            try:
                # Find the issue in Linear
                if not update.issue_id and update.issue_identifier:
                    issue = await linear_service.get_issue_by_identifier(update.issue_identifier)
                    if issue:
                        update.issue_id = issue.get("id")
                        update.issue_title = issue.get("title")
                
                if update.issue_id:
                    # Post comment to the issue
                    comment = await self._generate_linear_comment(update)
                    result = await linear_service.add_comment(update.issue_id, comment)
                    if result.get("success"):
                        linear_comments += 1
                        logger.info(f"[Summary] Posted comment to {update.issue_identifier}")
                    
                    # Update estimate if provided
                    if update.estimate_days:
                        await linear_service.update_issue_estimate(
                            update.issue_id, 
                            update.estimate_days
                        )
                    
                    # Create escalation if needed
                    if update.escalation_needed:
                        escalation = await self._create_escalation(
                            team_id=team_id,
                            parent_issue=update,
                        )
                        if escalation:
                            escalations_created.append(escalation)
                            logger.info(f"[Summary] Created escalation ticket: {escalation.get('identifier')}")
                            
            except Exception as e:
                error_msg = f"Error processing {update.issue_identifier}: {str(e)}"
                logger.info(f"[Summary] {error_msg}")
                errors.append(error_msg)
        
        # Step 4: Generate summary
        try:
            summary_text = await reasoning_service.generate_standup_summary(
                [asdict(u) for u in issue_updates],
                team_id
            )
        except Exception as e:
            logger.info(f"[Summary] Error generating summary: {e}")
            summary_text = self._generate_fallback_summary(issue_updates)
            errors.append(f"Summary generation error: {str(e)}")
        
        # Step 5: Post to Slack
        slack_posted = False
        if slack_channel_id:
            try:
                slack_result = await self._post_slack_summary(
                    channel_id=slack_channel_id,
                    summary_text=summary_text,
                    issue_updates=issue_updates,
                    escalations=escalations_created
                )
                slack_posted = slack_result.get("ok", False)
                logger.info(f"[Summary] Slack post result: {slack_posted}")
            except Exception as e:
                logger.info(f"[Summary] Error posting to Slack: {e}")
                errors.append(f"Slack error: {str(e)}")
        
        result = SummaryResult(
            standup_id=standup_id,
            processed_at=datetime.now(),
            total_updates=len(issue_updates),
            linear_comments_posted=linear_comments,
            escalations_created=escalations_created,
            slack_posted=slack_posted,
            summary_text=summary_text,
            issue_updates=[asdict(u) for u in issue_updates],
            errors=errors
        )
        
        logger.info(f"[Summary] Processing complete: {linear_comments} comments, "
              f"{len(escalations_created)} escalations, Slack: {slack_posted}")
        
        return result
    
    def _format_conversation(
        self, 
        user_transcripts: List[Dict], 
        agent_transcripts: List[Dict]
    ) -> str:
        """Combine transcripts into a readable conversation format"""
        # Merge and sort by timestamp
        all_messages = []
        
        for t in user_transcripts:
            all_messages.append({
                "speaker": "Developer",
                "text": t.get("text", ""),
                "timestamp": t.get("timestamp", 0)
            })
        
        for t in agent_transcripts:
            all_messages.append({
                "speaker": "AI Moderator",
                "text": t.get("text", ""),
                "timestamp": t.get("timestamp", 0)
            })
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x["timestamp"])
        
        # Format as conversation
        lines = []
        for msg in all_messages:
            if msg["text"]:
                lines.append(f"{msg['speaker']}: {msg['text']}")
        
        return "\n".join(lines)
    
    async def _extract_issue_updates(
        self, 
        conversation: str,
        known_issues: List[Dict] = None
    ) -> List[IssueUpdate]:
        """Use LLM to extract structured issue updates from conversation"""
        
        logger.info(f"[Summary] Extracting issues from conversation ({len(conversation)} chars)")
        logger.info(f"[Summary] Known issues: {known_issues}")
        logger.info(f"[Summary] Conversation content:\n{conversation[:1000]}...")
        
        system_prompt = """You are an AI that extracts structured updates from standup meeting transcripts.

Analyze the conversation and extract updates for each issue discussed. Look for:
1. Issue identifiers (e.g., NEO-7, NEO-8, ENG-123, or any PROJECT-NUMBER format)
2. Status updates (progressing, blocked, completed, at_risk)
3. Blockers or obstacles
4. Dependencies on other teams
5. Estimated completion time (extract as number of days if possible)
6. Next steps
7. Whether escalation is needed

Return a JSON array of issue updates. Each update should have:
{
    "issue_identifier": "NEO-7",
    "status": "progressing|blocked|completed|at_risk",
    "blockers": "description or null",
    "dependencies": "team/person or null",
    "estimate_days": number or null,
    "eta": "date string or null",
    "next_steps": "description or null",
    "escalation_needed": true/false,
    "escalation_reason": "reason or null",
    "transcript_snippet": "relevant quote from conversation"
}

IMPORTANT: If no specific issue IDs are mentioned in the conversation but you can infer which issue from the known issues list, use that issue identifier.
If no issues are mentioned at all, return an empty array [].
Return ONLY valid JSON, no other text."""

        # Build context about known issues
        known_issues_text = ""
        if known_issues:
            issue_details = []
            for i in known_issues:
                assignee = i.get('assignee', {})
                assignee_name = assignee.get('name', 'Unassigned') if isinstance(assignee, dict) else 'Unassigned'
                issue_details.append(f"- {i.get('identifier')}: {i.get('title')} (Assigned to: {assignee_name})")
            known_issues_text = f"\n\nKnown issues being tracked:\n" + "\n".join(issue_details)

        prompt = f"""Standup Conversation:
---
{conversation}
---
{known_issues_text}

Extract all issue updates from this conversation. If the developer mentions working on something that matches a known issue above, use that issue's identifier."""

        try:
            logger.info(f"[Summary] Calling LLM for extraction...")
            response = await reasoning_service._call_llm(prompt, system_prompt)
            logger.info(f"[Summary] LLM response: {response[:500]}...")
            
            # Clean up response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            updates_data = json.loads(response.strip())
            logger.info(f"[Summary] Parsed {len(updates_data)} issue updates from LLM")
            
            # Convert to IssueUpdate objects
            updates = []
            for data in updates_data:
                logger.info(f"[Summary] Issue update: {data.get('issue_identifier')} - {data.get('status')}")
                updates.append(IssueUpdate(
                    issue_identifier=data.get("issue_identifier", "UNKNOWN"),
                    status=data.get("status", "progressing"),
                    blockers=data.get("blockers"),
                    dependencies=data.get("dependencies"),
                    estimate_days=data.get("estimate_days"),
                    eta=data.get("eta"),
                    next_steps=data.get("next_steps"),
                    escalation_needed=data.get("escalation_needed", False),
                    escalation_reason=data.get("escalation_reason"),
                    transcript_snippet=data.get("transcript_snippet")
                ))
            
            return updates
            
        except Exception as e:
            logger.error(f"[Summary] LLM extraction error: {e}")
            import traceback
            logger.error(f"[Summary] Traceback: {traceback.format_exc()}")
            return []
    
    async def _generate_linear_comment(self, update: IssueUpdate) -> str:
        """Generate formatted comment for Linear issue"""
        return await reasoning_service.generate_linear_comment(
            status=update.status,
            blockers=update.blockers,
            dependencies=update.dependencies,
            eta=update.eta,
            next_steps=update.next_steps,
            escalation_needed=update.escalation_needed,
            escalation_reason=update.escalation_reason
        )
    
    async def _create_escalation(
        self,
        team_id: str,
        parent_issue: IssueUpdate
    ) -> Optional[Dict]:
        """Create an escalation ticket in Linear"""
        title = f"[ESCALATION] {parent_issue.issue_identifier}: {parent_issue.escalation_reason or 'Requires attention'}"
        
        description = f"""## Escalation from Standup

**Original Issue:** {parent_issue.issue_identifier} - {parent_issue.issue_title or 'N/A'}

**Reason for Escalation:**
{parent_issue.escalation_reason or 'Issue requires immediate attention'}

**Current Status:** {parent_issue.status}

**Blockers:**
{parent_issue.blockers or 'None specified'}

**Dependencies:**
{parent_issue.dependencies or 'None specified'}

---
*This ticket was automatically created by StandupAI*
"""
        
        result = await linear_service.create_escalation_issue(
            team_id=team_id,
            title=title,
            description=description,
            parent_issue_id=parent_issue.issue_id,
            priority=1  # Urgent
        )
        
        if result.get("success"):
            issue = result.get("issue", {})
            return {
                "identifier": issue.get("identifier"),
                "id": issue.get("id"),
                "url": issue.get("url"),
                "original_issue": parent_issue.issue_identifier
            }
        
        return None
    
    async def _post_slack_summary(
        self,
        channel_id: str,
        summary_text: str,
        issue_updates: List[IssueUpdate],
        escalations: List[Dict]
    ) -> Dict:
        """Post formatted summary to Slack channel - Simple Digest Format"""
        
        today = datetime.now().strftime('%b %d')
        
        # Build simple text message (no blocks - cleaner format)
        lines = [
            f"*📋 Daily Standup Digest — {today}*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        
        # Add each issue update
        for update in issue_updates:
            # Determine status emoji and text
            status_map = {
                "progressing": "Progressing",
                "completed": "Completed ✅",
                "blocked": "Blocked 🔴",
                "at_risk": "At Risk ⚠️"
            }
            status_text = status_map.get(update.status, update.status.title())
            
            lines.append("")
            lines.append(f"*Issue:* {update.issue_identifier} ({update.issue_title or 'N/A'})")
            lines.append(f"*Status:* {status_text}")
            
            if update.eta:
                lines.append(f"*ETA:* {update.eta}")
            
            if update.blockers:
                lines.append(f"*Blockers:* {update.blockers}")
            else:
                lines.append("*Blockers:* None")
            
            if update.next_steps:
                lines.append(f"*Action:* {update.next_steps}")
            
            if update.new_assignee_email:
                lines.append(f"*Working Person:* {update.new_assignee_email}")
            
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Add escalations if any
        if escalations:
            lines.append("")
            lines.append("*🚨 Escalations Created:*")
            for e in escalations:
                lines.append(f"• {e.get('identifier')}: Created for {e.get('original_issue')}")
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        message_text = "\n".join(lines)
        
        return await slack_service.send_message(
            channel=channel_id,
            text=message_text
        )
    
    def _generate_fallback_summary(self, issue_updates: List[IssueUpdate]) -> str:
        """Generate a simple summary when LLM fails"""
        if not issue_updates:
            return "Standup completed. No specific issue updates were captured."
        
        lines = [f"Standup completed with {len(issue_updates)} issue updates:\n"]
        
        for update in issue_updates:
            status_emoji = {
                "progressing": "🔄",
                "blocked": "🔴", 
                "completed": "✅",
                "at_risk": "⚠️"
            }.get(update.status, "⚪")
            
            lines.append(f"{status_emoji} {update.issue_identifier}: {update.status.title()}")
            if update.blockers:
                lines.append(f"   Blockers: {update.blockers}")
            if update.eta:
                lines.append(f"   ETA: {update.eta}")
        
        return "\n".join(lines)


# Singleton instance
standup_summary_service = StandupSummaryService()
