"""Conversation context management for the chatbot."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from models import ConversationContext

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation contexts for the chatbot."""
    
    def __init__(self, max_context_length: int = 10, session_timeout_hours: int = 24):
        """
        Initialize the conversation manager.
        
        Args:
            max_context_length: Maximum number of messages to keep in context
            session_timeout_hours: Hours after which a session expires
        """
        self.conversations: Dict[str, ConversationContext] = {}
        self.max_context_length = max_context_length
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Session ID
        """
        if session_id and session_id in self.conversations:
            # Check if session is still valid
            session = self.conversations[session_id]
            if datetime.now() - session.updated_at < self.session_timeout:
                return session_id
            else:
                # Session expired, remove it
                del self.conversations[session_id]
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        self.conversations[new_session_id] = ConversationContext(
            session_id=new_session_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(f"Created new conversation session: {new_session_id}")
        return new_session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation context.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.get_or_create_session(session_id)
        
        conversation = self.conversations[session_id]
        
        # Add new message
        conversation.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim context if too long
        if len(conversation.messages) > self.max_context_length:
            conversation.messages = conversation.messages[-self.max_context_length:]
        
        # Update timestamp
        conversation.updated_at = datetime.now()
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages in the conversation
        """
        if session_id not in self.conversations:
            return []
        
        return self.conversations[session_id].messages.copy()
    
    def clear_session(self, session_id: str):
        """
        Clear a conversation session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation session: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired conversation sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, conversation in self.conversations.items():
            if current_time - conversation.updated_at > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.conversations[session_id]
            logger.info(f"Removed expired session: {session_id}")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_stats(self) -> Dict[str, int]:
        """
        Get statistics about active sessions.
        
        Returns:
            Dictionary with session statistics
        """
        return {
            'active_sessions': len(self.conversations),
            'total_messages': sum(len(conv.messages) for conv in self.conversations.values())
        }

# Global instance
conversation_manager = ConversationManager()
