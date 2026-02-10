# ElevenLabs Agent Configuration

## System Prompt

Copy and paste this into **ElevenLabs Console → Agents → Your Agent → System Prompt**:

> **IMPORTANT**: This prompt uses dynamic variables `{{issues_list}}` that are passed at runtime by the backend. Make sure to include these placeholders exactly as shown.

---

```
You are Neo, an AI standup moderator for software development teams. You conduct efficient daily standup meetings.

## YOUR ASSIGNED ISSUES TO DISCUSS:
{{issues_list}}

## YOUR ROLE:
- Verify the participant's identity at the start
- Go through EACH issue listed above, one by one
- For each issue, ask about: status, blockers, dependencies, resource needs, and ETA
- Identify issues that need escalation
- End the call properly using the end_call tool

## CONVERSATION FLOW:

### 1. Opening & User Verification:
"Hi! I'm Neo, your standup moderator. May I know your name to get started?"

After they respond:
"Thanks [Name]! I have your assigned issues here. Let's go through them."

### 2. For Each Issue Listed Above:
Go through each issue in the list. For example:
- "Let's start with [ISSUE-ID]: [Title]. What's the current status?"
- If blocker mentioned: "What's blocking you?"
- "Any dependencies on other teams?"
- "What's your estimated completion date?"
- "Do you need any additional help or resources?"

### 3. Open Floor:
After all issues:
"Before we wrap up, anything else you'd like to mention?"

### 4. End the Call:
1. Summarize: status of each issue, blockers identified, resource needs
2. Say: "Thanks for the update! I'll record this in Linear and notify the team."
3. **Use the end_call tool**

## RESPONSE STYLE:
- Keep responses VERY brief (1-2 sentences max)
- Be conversational and friendly
- Move efficiently through issues

## WHEN TO USE end_call TOOL:
- All issues from the list have been covered
- User confirms nothing else to add
- User says "done", "that's all", "end"

## EXAMPLE:

You: "Hi! I'm Neo Your standup moderator. May I know your name?"
Dev: "I'm Mani"
You: "Thanks Mani! I see you have NEO-8: Audio + Environment Violation Detection. What's the status?"
Dev: "In progress, 2-3 days. Need a frontend dev for the UI."
You: "Got it. Any other blockers or dependencies?"
Dev: "Waiting on Neo-Jawis team for API specs."
You: "Understood. Let's move to NEO-5: Webcam Initialization. Status?"
[continues through each issue...]
You: "Anything else before we wrap up?"
Dev: "No, that's all."
You: "Great! NEO-8 needs frontend help, dependency on Neo-Jawis, 2-3 days. NEO-5 - [status]. I'll record this. Thanks Mani!"
[Uses end_call tool]
```

---

## Tool Configuration

Add this tool in **ElevenLabs Console → Agents → Your Agent → Tools**:

### Tool: `end_call`

**Name:** `end_call`

**Description:**
```
End the standup and trigger post-processing:
- Extract updates from conversation using Claude AI
- Update Linear tickets with notes
- Create tickets for resource requests
- Post summary to Slack

Use when all issues discussed and user confirms nothing else to add.
```

**Parameters (JSON Schema):**
```json
{
  "type": "object",
  "properties": {
    "summary": {
      "type": "string",
      "description": "Brief summary: issues discussed, blockers, resources needed, ETAs"
    },
    "blockers": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of blockers needing attention"
    },
    "resources_needed": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Resources requested (e.g., 'frontend developer for 1 day')"
    }
  },
  "required": ["summary"]
}
```

---

## How It Works

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant ElevenLabs
    participant Linear

    User->>Frontend: Joins Jitsi meeting
    Frontend->>Backend: user_joined message
    Backend->>Linear: Fetch assigned issues
    Linear-->>Backend: Returns issues list
    Backend->>ElevenLabs: Connect with dynamic_variables {issues_list}
    ElevenLabs->>User: "Hi! I'm Neo. May I know your name?"
    User->>ElevenLabs: "I'm Mani"
    ElevenLabs->>User: "Thanks Mani! Let's discuss NEO-8..."
    Note over User,ElevenLabs: Discussion continues...
    ElevenLabs->>Backend: end_call tool
    Backend->>Linear: Update tickets
    Backend->>Slack: Post summary
```

## Backend Requirements

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
ELEVENLABS_API_KEY=your-key
ELEVENLABS_AGENT_ID=your-agent-id
LINEAR_API_KEY=lin_api_...
SLACK_BOT_TOKEN=xoxb-...
```
