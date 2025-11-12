"""
Session Manager with Cookie Persistence
Handles authentication token persistence across browser sessions and redirects
"""
import streamlit as st
import extra_streamlit_components as stx
import json
from typing import Optional, Dict, Any
from config import SESSION_USER, SESSION_ACCESS_TOKEN, SESSION_REFRESH_TOKEN


class SessionManager:
    """Manages user session with cookie persistence"""

    def __init__(self):
        """Initialize cookie manager"""
        # Use a unique key to avoid conflicts
        if '_cookie_manager' not in st.session_state:
            st.session_state._cookie_manager = stx.CookieManager(key='session_cookie_manager')
        self.cookie_manager = st.session_state._cookie_manager

        # Flag to track if we've already restored in this render
        if '_session_restored' not in st.session_state:
            st.session_state._session_restored = False

    def save_session(self, user_data: Dict[str, Any], access_token: str, refresh_token: str):
        """
        Save session data to both session state and cookies

        Args:
            user_data: User information dictionary
            access_token: JWT access token
            refresh_token: JWT refresh token
        """
        # Save to session state
        st.session_state[SESSION_USER] = user_data
        st.session_state[SESSION_ACCESS_TOKEN] = access_token
        st.session_state[SESSION_REFRESH_TOKEN] = refresh_token

        # Save to cookies (persistent)
        self.cookie_manager.set('user', json.dumps(user_data), max_age=7*24*60*60)  # 7 days
        self.cookie_manager.set('access_token', access_token, max_age=24*60*60)  # 1 day
        self.cookie_manager.set('refresh_token', refresh_token, max_age=7*24*60*60)  # 7 days

    def restore_session(self) -> bool:
        """
        Restore session from cookies if session state is empty

        Returns:
            True if session was restored, False otherwise
        """
        # Check if session already exists in session state
        if SESSION_USER in st.session_state and SESSION_ACCESS_TOKEN in st.session_state:
            return True

        # Check if we've already attempted restoration in this render cycle
        if st.session_state._session_restored:
            return False

        # Mark that we've attempted restoration
        st.session_state._session_restored = True

        # Try to restore from cookies
        try:
            # Wait for cookie manager to be ready
            all_cookies = self.cookie_manager.get_all()

            if all_cookies:
                user_cookie = all_cookies.get('user')
                access_token = all_cookies.get('access_token')
                refresh_token = all_cookies.get('refresh_token')

                if user_cookie and access_token:
                    # Restore session state from cookies
                    st.session_state[SESSION_USER] = json.loads(user_cookie)
                    st.session_state[SESSION_ACCESS_TOKEN] = access_token
                    if refresh_token:
                        st.session_state[SESSION_REFRESH_TOKEN] = refresh_token
                    return True
        except Exception as e:
            # If restoration fails, silently ignore
            return False

        return False

    def clear_session(self):
        """Clear session from both session state and cookies"""
        # Clear session state
        if SESSION_USER in st.session_state:
            del st.session_state[SESSION_USER]
        if SESSION_ACCESS_TOKEN in st.session_state:
            del st.session_state[SESSION_ACCESS_TOKEN]
        if SESSION_REFRESH_TOKEN in st.session_state:
            del st.session_state[SESSION_REFRESH_TOKEN]

        # Reset restoration flag
        st.session_state._session_restored = False

        # Clear cookies
        try:
            self.cookie_manager.delete('user')
            self.cookie_manager.delete('access_token')
            self.cookie_manager.delete('refresh_token')
        except:
            pass

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated (checks session state and cookies)

        Returns:
            True if authenticated, False otherwise
        """
        # First try to restore from cookies if needed
        self.restore_session()

        # Then check session state
        return SESSION_USER in st.session_state and SESSION_ACCESS_TOKEN in st.session_state


# Global session manager instance
def get_session_manager() -> SessionManager:
    """Get or create global session manager instance"""
    if 'session_manager' not in st.session_state:
        st.session_state['session_manager'] = SessionManager()
    return st.session_state['session_manager']
