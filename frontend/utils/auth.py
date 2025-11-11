"""
Authentication utilities for Streamlit
"""
import streamlit as st
from config import SESSION_USER, SESSION_ACCESS_TOKEN


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return SESSION_USER in st.session_state and SESSION_ACCESS_TOKEN in st.session_state


def require_auth():
    """Decorator to require authentication"""
    if not is_authenticated():
        st.warning("Please login to access this page")
        st.stop()


def get_current_user():
    """Get current user from session"""
    return st.session_state.get(SESSION_USER, None)
