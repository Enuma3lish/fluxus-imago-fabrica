"""
API Client for backend communication
"""
import requests
import streamlit as st
from typing import Optional, Dict, Any
from config import *


class APIClient:
    """API Client for communicating with backend services"""

    def __init__(self):
        self.backend_url = BACKEND_URL
        self.payment_url = PAYMENT_SERVICE_URL

    def get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get request headers with authentication token"""
        headers = {
            'Content-Type': 'application/json',
        }

        if include_auth and SESSION_ACCESS_TOKEN in st.session_state:
            headers['Authorization'] = f"Bearer {st.session_state[SESSION_ACCESS_TOKEN]}"

        return headers

    def handle_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """Handle API response"""
        if response.status_code == 401:
            # Token expired, try to refresh
            if self.refresh_token():
                return None  # Retry the request
            else:
                st.session_state.clear()
                st.error("Session expired. Please login again.")
                return None

        if response.status_code >= 400:
            try:
                error_data = response.json()
                st.error(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                st.error(f"Error: {response.status_code}")
            return None

        return response.json()

    def refresh_token(self) -> bool:
        """Refresh access token"""
        if SESSION_REFRESH_TOKEN not in st.session_state:
            return False

        try:
            response = requests.post(
                API_AUTH_REFRESH,
                json={'refresh': st.session_state[SESSION_REFRESH_TOKEN]}
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state[SESSION_ACCESS_TOKEN] = data['access']
                return True
        except:
            pass

        return False

    def register(self, username: str, email: str, password: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Register a new user"""
        try:
            response = requests.post(
                API_AUTH_REGISTER,
                json={
                    'username': username,
                    'email': email,
                    'password': password,
                    'password_confirm': password,
                    **kwargs
                }
            )
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Registration failed: {str(e)}")
            return None

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login user"""
        try:
            response = requests.post(
                API_AUTH_LOGIN,
                json={'email': email, 'password': password}
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state[SESSION_USER] = data['user']
                st.session_state[SESSION_ACCESS_TOKEN] = data['tokens']['access']
                st.session_state[SESSION_REFRESH_TOKEN] = data['tokens']['refresh']
                return data
            else:
                return self.handle_response(response)

        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return None

    def logout(self) -> bool:
        """Logout user"""
        try:
            requests.post(API_AUTH_LOGOUT, headers=self.get_headers())
            st.session_state.clear()
            return True
        except:
            st.session_state.clear()
            return False

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user details"""
        try:
            response = requests.get(API_USERS_ME, headers=self.get_headers())
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Failed to get user: {str(e)}")
            return None

    def get_plans(self) -> Optional[list]:
        """Get all available plans"""
        try:
            response = requests.get(API_PLANS, headers=self.get_headers(include_auth=False))
            data = self.handle_response(response)
            return data.get('results', []) if data else []
        except Exception as e:
            st.error(f"Failed to get plans: {str(e)}")
            return []

    def get_subscriptions(self) -> Optional[list]:
        """Get user subscriptions"""
        try:
            response = requests.get(API_SUBSCRIPTIONS, headers=self.get_headers())
            data = self.handle_response(response)
            return data.get('results', []) if data else []
        except Exception as e:
            st.error(f"Failed to get subscriptions: {str(e)}")
            return []

    def create_subscription(self, plan_id: str, auto_renew: bool = True) -> Optional[Dict[str, Any]]:
        """Create a new subscription"""
        try:
            response = requests.post(
                API_SUBSCRIPTIONS,
                json={'plan_id': plan_id, 'auto_renew': auto_renew},
                headers=self.get_headers()
            )
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Failed to create subscription: {str(e)}")
            return None

    def update_subscription_status(self, subscription_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update subscription status"""
        try:
            response = requests.patch(
                f"{API_SUBSCRIPTIONS}{subscription_id}/update_status/",
                json={'status': status},
                headers=self.get_headers()
            )
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Failed to update subscription: {str(e)}")
            return None

    def get_orders(self) -> Optional[list]:
        """Get user orders"""
        try:
            response = requests.get(API_ORDERS, headers=self.get_headers())
            data = self.handle_response(response)
            return data.get('results', []) if data else []
        except Exception as e:
            st.error(f"Failed to get orders: {str(e)}")
            return []

    def create_order(self, plan_id: str, payment_method: str, notes: str = "") -> Optional[Dict[str, Any]]:
        """Create a new order"""
        try:
            response = requests.post(
                API_ORDERS,
                json={
                    'plan_id': plan_id,
                    'payment_method': payment_method,
                    'notes': notes
                },
                headers=self.get_headers()
            )
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Failed to create order: {str(e)}")
            return None

    def create_payment(self, order_id: str, amount: int, item_name: str, payment_method: str) -> Optional[Dict[str, Any]]:
        """Create payment with ECPay"""
        try:
            response = requests.post(
                API_PAYMENT_CREATE,
                json={
                    'order_id': order_id,
                    'amount': amount,
                    'item_name': item_name,
                    'payment_method': payment_method
                },
                headers=self.get_headers()
            )
            return self.handle_response(response)
        except Exception as e:
            st.error(f"Failed to create payment: {str(e)}")
            return None

    def get_invoices(self) -> Optional[list]:
        """Get user invoices"""
        try:
            response = requests.get(API_INVOICES, headers=self.get_headers())
            data = self.handle_response(response)
            return data.get('results', []) if data else []
        except Exception as e:
            st.error(f"Failed to get invoices: {str(e)}")
            return []
