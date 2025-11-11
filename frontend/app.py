"""
Streamlit Frontend - Main Application
"""
import streamlit as st
from streamlit_option_menu import option_menu
from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils.api_client import APIClient
from utils.auth import is_authenticated, get_current_user

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Initialize API client
api_client = APIClient()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .plan-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .plan-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border-color: #667eea;
    }
    .popular-badge {
        background-color: #ffd700;
        color: #000;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


def show_login_page():
    """Login page"""
    st.markdown('<h1 class="main-header">🎨 Fluxus Imago Fabrica</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Login to your account")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Logging in..."):
                            result = api_client.login(email, password)
                            if result:
                                st.success("Login successful!")
                                st.rerun()

        with tab2:
            st.subheader("Create a new account")
            with st.form("register_form"):
                username = st.text_input("Username", placeholder="username")
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                password_confirm = st.text_input("Confirm Password", type="password")
                first_name = st.text_input("First Name", placeholder="First Name")
                last_name = st.text_input("Last Name", placeholder="Last Name")

                submit = st.form_submit_button("Register", use_container_width=True)

                if submit:
                    if not username or not email or not password:
                        st.error("Please fill in all required fields")
                    elif password != password_confirm:
                        st.error("Passwords don't match")
                    else:
                        with st.spinner("Creating account..."):
                            result = api_client.register(
                                username=username,
                                email=email,
                                password=password,
                                first_name=first_name,
                                last_name=last_name
                            )
                            if result:
                                st.success("Registration successful! Please login.")


def show_dashboard():
    """Main dashboard"""
    user = get_current_user()

    st.markdown(f'<h1 class="main-header">Welcome, {user["username"]}! 👋</h1>', unsafe_allow_html=True)

    # Get user data
    subscriptions = api_client.get_subscriptions()
    orders = api_client.get_orders()

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Subscriptions", len([s for s in subscriptions if s['status'] == 'active']))

    with col2:
        st.metric("Total Orders", len(orders))

    with col3:
        completed_orders = len([o for o in orders if o['status'] == 'completed'])
        st.metric("Completed Payments", completed_orders)

    with col4:
        total_spent = sum([float(o['amount']) for o in orders if o['status'] == 'completed'])
        st.metric("Total Spent", f"${total_spent:.2f}")

    st.divider()

    # Recent subscriptions
    st.subheader("📋 Your Subscriptions")
    if subscriptions:
        for sub in subscriptions[:5]:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{sub['plan']['name']}**")
                with col2:
                    st.write(f"Status: **{sub['status'].upper()}**")
                with col3:
                    st.write(f"${sub['plan']['price']}/{sub['plan']['billing_cycle']}")
                with col4:
                    if sub['status'] == 'active' and st.button("Cancel", key=f"cancel_{sub['id']}"):
                        result = api_client.update_subscription_status(sub['id'], 'cancelled')
                        if result:
                            st.success("Subscription cancelled")
                            st.rerun()
                st.divider()
    else:
        st.info("No active subscriptions. Browse plans to get started!")

    st.divider()

    # Recent orders
    st.subheader("💳 Recent Orders")
    if orders:
        for order in orders[:5]:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                with col1:
                    st.write(f"**{order['order_number']}**")
                with col2:
                    status_color = {
                        'pending': '🟡',
                        'processing': '🔵',
                        'completed': '🟢',
                        'failed': '🔴',
                        'cancelled': '⚫'
                    }
                    st.write(f"{status_color.get(order['status'], '⚪')} {order['status'].upper()}")
                with col3:
                    st.write(f"${order['amount']}")
                with col4:
                    st.write(order['created_at'][:10])
                st.divider()
    else:
        st.info("No orders yet")


def show_plans_page():
    """Plans and pricing page"""
    st.markdown('<h1 class="main-header">💎 Choose Your Plan</h1>', unsafe_allow_html=True)

    plans = api_client.get_plans()

    if not plans:
        st.error("Failed to load plans")
        return

    # Display plans in columns
    cols = st.columns(min(len(plans), 3))

    for idx, plan in enumerate(plans):
        with cols[idx % 3]:
            with st.container():
                # Popular badge
                if plan.get('is_popular'):
                    st.markdown('<span class="popular-badge">⭐ POPULAR</span>', unsafe_allow_html=True)

                st.markdown(f"### {plan['name']}")
                st.markdown(f"## ${plan['price']}")
                st.markdown(f"*per {plan['billing_cycle']}*")

                st.markdown("---")

                # Features
                if plan.get('features'):
                    for key, value in plan['features'].items():
                        st.markdown(f"✓ {key}: {value}")

                st.markdown(f"✓ Max {plan['max_users']} users")
                st.markdown(f"✓ {plan['max_storage_gb']} GB storage")

                st.markdown("---")

                if st.button("Subscribe", key=f"plan_{plan['id']}", use_container_width=True):
                    st.session_state['selected_plan'] = plan
                    st.session_state['page'] = 'checkout'
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)


def show_checkout_page():
    """Checkout page"""
    if 'selected_plan' not in st.session_state:
        st.warning("Please select a plan first")
        return

    plan = st.session_state['selected_plan']

    st.markdown('<h1 class="main-header">🛒 Checkout</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Order Summary")
        st.write(f"**Plan:** {plan['name']}")
        st.write(f"**Price:** ${plan['price']}")
        st.write(f"**Billing Cycle:** {plan['billing_cycle']}")

        if plan.get('description'):
            st.write(f"**Description:** {plan['description']}")

        st.divider()

        st.subheader("Payment Method")
        payment_method = st.selectbox(
            "Select Payment Method",
            options=["Credit", "ATM", "CVS", "BARCODE"],
            format_func=lambda x: {
                "Credit": "💳 Credit Card",
                "ATM": "🏦 ATM Transfer",
                "CVS": "🏪 Convenience Store",
                "BARCODE": "📊 Barcode"
            }[x]
        )

        notes = st.text_area("Notes (Optional)", placeholder="Add any notes here...")

    with col2:
        st.subheader("Price Details")
        st.write(f"Plan Price: ${plan['price']}")
        st.write(f"Tax (5%): ${float(plan['price']) * 0.05:.2f}")
        st.write("---")
        total = float(plan['price']) * 1.05
        st.write(f"**Total: ${total:.2f}**")

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("Proceed to Payment", use_container_width=True, type="primary"):
            with st.spinner("Creating order..."):
                # Create order
                order = api_client.create_order(
                    plan_id=plan['id'],
                    payment_method=payment_method.lower().replace(' ', '_'),
                    notes=notes
                )

                if order:
                    # Create payment
                    payment = api_client.create_payment(
                        order_id=order['id'],
                        amount=int(float(plan['price'])),
                        item_name=plan['name'],
                        payment_method=payment_method
                    )

                    if payment and payment.get('success'):
                        # Store payment info and redirect
                        st.session_state['payment_data'] = payment
                        st.session_state['order'] = order
                        st.success("Order created! Redirecting to payment...")

                        # Generate ECPay form
                        form_html = f"""
                        <html>
                        <body>
                        <form id="ecpay_form" method="post" action="{payment['payment_url']}">
                        """
                        for key, value in payment['form_data'].items():
                            form_html += f'<input type="hidden" name="{key}" value="{value}">'
                        form_html += """
                        </form>
                        <script>document.getElementById('ecpay_form').submit();</script>
                        </body>
                        </html>
                        """

                        st.components.v1.html(form_html, height=0)
                    else:
                        st.error("Failed to create payment")


def show_invoices_page():
    """Invoices page"""
    st.markdown('<h1 class="main-header">📄 Invoices</h1>', unsafe_allow_html=True)

    invoices = api_client.get_invoices()

    if not invoices:
        st.info("No invoices yet")
        return

    for invoice in invoices:
        with st.expander(f"Invoice {invoice['invoice_number']} - ${invoice['total_amount']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Invoice Number:** {invoice['invoice_number']}")
                st.write(f"**Amount:** ${invoice['amount']}")
                st.write(f"**Tax:** ${invoice['tax_amount']}")
                st.write(f"**Total:** ${invoice['total_amount']}")

            with col2:
                st.write(f"**Issued:** {invoice['issued_at'][:10]}")
                if invoice.get('paid_at'):
                    st.write(f"**Paid:** {invoice['paid_at'][:10]}")
                st.write(f"**Currency:** {invoice['currency']}")

            if invoice.get('pdf_url'):
                st.link_button("Download PDF", invoice['pdf_url'])


def main():
    """Main application"""
    # Check if user is authenticated
    if not is_authenticated():
        show_login_page()
        return

    # Sidebar navigation
    with st.sidebar:
        user = get_current_user()
        st.write(f"👤 **{user['username']}**")
        st.write(f"📧 {user['email']}")
        st.divider()

        selected = option_menu(
            menu_title="Navigation",
            options=["Dashboard", "Plans", "Invoices", "Settings"],
            icons=["speedometer2", "gem", "file-text", "gear"],
            default_index=0,
        )

        st.divider()

        if st.button("Logout", use_container_width=True):
            api_client.logout()
            st.rerun()

    # Show selected page
    if 'page' in st.session_state and st.session_state['page'] == 'checkout':
        show_checkout_page()
    elif selected == "Dashboard":
        show_dashboard()
    elif selected == "Plans":
        show_plans_page()
    elif selected == "Invoices":
        show_invoices_page()
    elif selected == "Settings":
        st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
        st.info("Settings page coming soon!")


if __name__ == "__main__":
    main()
