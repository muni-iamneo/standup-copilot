"""
Email Service
Handles SMTP email sending for PM summaries
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime
from app.config import settings


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
    
    def _create_html_summary(
        self,
        team_name: str,
        standup_date: datetime,
        progress_issues: List[Dict],
        blocked_issues: List[Dict],
        at_risk_issues: List[Dict],
        escalations: List[Dict]
    ) -> str:
        """Create HTML email content for PM summary"""
        
        date_str = standup_date.strftime("%B %d, %Y")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 5px 0 0;
            opacity: 0.9;
        }}
        .content {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 0 0 10px 10px;
        }}
        .section {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .progress {{ border-left: 4px solid #10b981; }}
        .blocked {{ border-left: 4px solid #ef4444; }}
        .at-risk {{ border-left: 4px solid #f59e0b; }}
        .escalation {{ border-left: 4px solid #8b5cf6; }}
        .issue-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .issue-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .issue-list li:last-child {{
            border-bottom: none;
        }}
        .issue-id {{
            font-weight: 600;
            color: #4f46e5;
        }}
        .empty-state {{
            color: #6b7280;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #6b7280;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Standup Summary</h1>
        <p>{team_name} • {date_str}</p>
    </div>
    <div class="content">
        <div class="section progress">
            <div class="section-title">✅ Progress ({len(progress_issues)} issues)</div>
            <ul class="issue-list">
"""
        
        if progress_issues:
            for issue in progress_issues:
                html += f'<li><span class="issue-id">{issue.get("identifier", "N/A")}</span>: {issue.get("title", "Untitled")}</li>'
        else:
            html += '<li class="empty-state">No issues in progress</li>'
        
        html += f"""
            </ul>
        </div>
        
        <div class="section blocked">
            <div class="section-title">🔴 Blocked ({len(blocked_issues)} issues)</div>
            <ul class="issue-list">
"""
        
        if blocked_issues:
            for issue in blocked_issues:
                html += f'<li><span class="issue-id">{issue.get("identifier", "N/A")}</span>: {issue.get("title", "Untitled")}<br><small>Blockers: {issue.get("blockers", "Unknown")}</small></li>'
        else:
            html += '<li class="empty-state">No blocked issues 🎉</li>'
        
        html += f"""
            </ul>
        </div>
        
        <div class="section at-risk">
            <div class="section-title">⚠️ At Risk ({len(at_risk_issues)} issues)</div>
            <ul class="issue-list">
"""
        
        if at_risk_issues:
            for issue in at_risk_issues:
                html += f'<li><span class="issue-id">{issue.get("identifier", "N/A")}</span>: {issue.get("title", "Untitled")}</li>'
        else:
            html += '<li class="empty-state">No at-risk issues</li>'
        
        html += f"""
            </ul>
        </div>
        
        <div class="section escalation">
            <div class="section-title">🚨 Escalations Created ({len(escalations)})</div>
            <ul class="issue-list">
"""
        
        if escalations:
            for esc in escalations:
                html += f'<li><span class="issue-id">{esc.get("new_ticket_id", "N/A")}</span>: Created for {esc.get("original_issue_id", "N/A")}</li>'
        else:
            html += '<li class="empty-state">No escalations created</li>'
        
        html += """
            </ul>
        </div>
    </div>
    <div class="footer">
        <p>Generated by StandupAI • Your AI-powered standup assistant</p>
    </div>
</body>
</html>
"""
        return html
    
    def send_pm_summary_email(
        self,
        to_email: str,
        team_name: str,
        standup_date: datetime,
        progress_issues: List[Dict],
        blocked_issues: List[Dict],
        at_risk_issues: List[Dict],
        escalations: List[Dict]
    ) -> bool:
        """Send PM summary email"""
        
        if not self.smtp_user or not self.smtp_password:
            print("SMTP credentials not configured")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"📊 Standup Summary - {team_name} - {standup_date.strftime('%b %d, %Y')}"
            message["From"] = self.from_email
            message["To"] = to_email
            
            # Plain text version
            text_content = f"""
Standup Summary - {team_name}
Date: {standup_date.strftime('%B %d, %Y')}

✅ Progress: {len(progress_issues)} issues
🔴 Blocked: {len(blocked_issues)} issues
⚠️ At Risk: {len(at_risk_issues)} issues
🚨 Escalations: {len(escalations)} created

View full details in your dashboard.

-- StandupAI
"""
            
            # HTML version
            html_content = self._create_html_summary(
                team_name,
                standup_date,
                progress_issues,
                blocked_issues,
                at_risk_issues,
                escalations
            )
            
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False


# Singleton instance
email_service = EmailService()
