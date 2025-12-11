"""
Jitsi Service
Handles Jitsi meeting URL generation and management
"""

import uuid
import jwt
import time
from typing import Optional, Dict
from app.config import settings


class JitsiService:
    """Service for Jitsi meeting management"""
    
    def __init__(self):
        self.domain = settings.JITSI_DOMAIN
        self.app_id = settings.JITSI_APP_ID
        self.private_key = settings.JITSI_PRIVATE_KEY
    
    def generate_meeting_url(self, prefix: str = "standup") -> str:
        """Generate a unique Jitsi meeting URL for 8x8.vc"""
        meeting_id = str(uuid.uuid4())[:12]  # Longer ID for uniqueness
        room_name = f"{prefix}-{meeting_id}"
        
        # For 8x8.vc with app ID
        if self.app_id:
            return f"https://{self.domain}/{self.app_id}/{room_name}"
        
        # Fallback to standard Jitsi
        return f"https://{self.domain}/{room_name}"
    
    def generate_jwt_token(
        self,
        room_name: str,
        user_name: str = "StandupAI Bot",
        user_email: str = "bot@standupai.com",
        is_moderator: bool = True,
        duration_minutes: int = 60
    ) -> Optional[str]:
        """
        Generate a JWT token for authenticated Jitsi access.
        Note: This requires Jitsi to be configured with JWT authentication.
        For meet.jit.si public server, JWT is not required.
        """
        if not self.private_key:
            return None
        
        current_time = int(time.time())
        expiry_time = current_time + (duration_minutes * 60)
        
        payload = {
            "iss": "standupai",
            "sub": self.domain,
            "aud": "jitsi",
            "room": room_name,
            "exp": expiry_time,
            "iat": current_time,
            "context": {
                "user": {
                    "name": user_name,
                    "email": user_email,
                    "moderator": is_moderator
                },
                "features": {
                    "recording": True,
                    "livestreaming": False,
                    "transcription": True
                }
            }
        }
        
        try:
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
            return token
        except Exception as e:
            print(f"Error generating JWT: {e}")
            return None
    
    def get_meeting_config(
        self,
        room_name: str,
        subject: str = "Daily Standup",
        start_audio_muted: bool = False,
        start_video_muted: bool = True,
        enable_recording: bool = True
    ) -> Dict:
        """Get configuration options for Jitsi meeting"""
        return {
            "roomName": room_name,
            "subject": subject,
            "configOverwrite": {
                "startWithAudioMuted": start_audio_muted,
                "startWithVideoMuted": start_video_muted,
                "enableRecording": enable_recording,
                "prejoinPageEnabled": False,
                "disableDeepLinking": True,
                "enableClosePage": True
            },
            "interfaceConfigOverwrite": {
                "SHOW_JITSI_WATERMARK": False,
                "SHOW_WATERMARK_FOR_GUESTS": False,
                "DEFAULT_REMOTE_DISPLAY_NAME": "Team Member",
                "TOOLBAR_BUTTONS": [
                    "microphone", "camera", "closedcaptions", "desktop",
                    "fullscreen", "fodeviceselection", "hangup", "chat",
                    "recording", "settings", "raisehand", "videoquality",
                    "filmstrip", "participants-pane", "tileview"
                ]
            }
        }
    
    def get_embed_url(
        self,
        room_name: str,
        jwt_token: Optional[str] = None
    ) -> str:
        """Get embeddable Jitsi URL with optional JWT"""
        base_url = f"https://{self.domain}/{room_name}"
        if jwt_token:
            return f"{base_url}?jwt={jwt_token}"
        return base_url


# Singleton instance
jitsi_service = JitsiService()
