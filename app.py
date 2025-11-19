import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Advanced Finance Tracker",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'recurring' not in st.session_state:
    st.session_state.recurring = []

# Helper functions
def add_transaction(date, category, amount, transaction_type, description, tags=None):
    """Add a new transaction"""
    transaction = {
        'date': date.strftime('%Y-%m-%d'),
        'category': category,
        'amount': float(amount),
        'type': transaction_type,
        'description': description,
        'tags': tags if tags else [],
        'id': len(st.session_state.transactions)
    }
    st.session_state.transactions.append(transaction)

def add_budget(category, amount, month):
    """Add a budget for a category"""
    key = f"{category}_{month}"
    st.session_state.budgets[key] = float(amount)

def add_goal(goal_name, target_amount, deadline, category):
    """Add a savings goal"""
    goal = {
        'name': goal_name,
        'target': float(target_amount),
        'deadline': deadline.strftime('%Y-%m-%d'),
        'category': category,
        'created': datetime.now().strftime('%Y-%m-%d')
    }
    st.session_state.goals.append(goal)

def add_recurring(category, amount, frequency, transaction_type):
    """Add a recurring transaction"""
    recurring = {
        'category': category,
        'amount': float(amount),
        'frequency': frequency,
        'type': transaction_type,
        'active': True
    }
    st.session_state.recurring.append(recurring)

def get_dataframe():
    """Convert transactions to DataFrame"""
    if not st.session_state.transactions:
        return pd.DataFrame(columns=['date', 'category', 'amount', 'type', 'description', 'tags'])
    df = pd.DataFrame(st.session_state.transactions)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_balance():
    """Calculate current balance"""
    df = get_dataframe()
    if df.empty:
        return 0
    income = df[df['type'] == 'Income']['amount'].sum()
    expenses = df[df['type'] == 'Expense']['amount'].sum()
    return income - expenses

def get_spending_by_category(df, month=None):
    """Get spending grouped by category"""
    expense_df = df[df['type'] == 'Expense'].copy()
    if month and not expense_df.empty:
        expense_df['month'] = expense_df['date'].dt.to_period('M')
        expense_df = expense_df[expense_df['month'] == month]
    return expense_df.groupby('category')['amount'].sum() if not expense_df.empty else pd.Series()

def check_budget_alerts(df):
    """Check if any budgets are exceeded"""
    alerts = []
    current_month = datetime.now().strftime('%Y-%m')
    
    for budget_key, budget_amount in st.session_state.budgets.items():
        category = budget_key.split('_')[0]
        spending = get_spending_by_category(df).get(category, 0)
        
        if spending > budget_amount:
            alerts.append({
                'category': category,
                'budget': budget_amount,
                'spent': spending,
                'over': spending - budget_amount
            })
    
    return alerts

def get_trend_data(df, days=30):
    """Get spending trend over time"""
    if df.empty:
        return None
    
    cutoff_date = datetime.now() - timedelta(days=days)
    df_recent = df[df['date'] >= cutoff_date].copy()
    
    if df_recent.empty:
        return None
    
    df_recent['date'] = df_recent['date'].dt.date
    trend = df_recent.groupby(['date', 'type'])['amount'].sum().reset_index()
    return trend

def calculate_category_stats(df):
    """Calculate statistics by category"""
    if df.empty:
        return {}
    
    stats = {}
    for category in df['category'].unique():
        cat_df = df[df['category'] == category]
        stats[category] = {
            'count': len(cat_df),
            'total': cat_df['amount'].sum(),
            'average': cat_df['amount'].mean(),
            'max': cat_df['amount'].max(),
            'min': cat_df['amount'].min()
        }
    return stats

def get_top_transactions(df, n=10):
    """Get top n transactions by amount"""
    if df.empty:
        return df
    return df.nlargest(n, 'amount')[['date', 'category', 'amount', 'type', 'description']]

# Main app
st.title("💰 Advanced Personal Finance Tracker")
st.markdown("**Professional Finance Management with Budgets, Goals & Insights**")

# Sidebar
with st.sidebar:
    st.header("📋 Navigation")
    page = st.selectbox(
        "Select Page",
        ["Dashboard", "Add Transaction", "Budgets", "Goals", "Recurring", "Analytics", "Insights", "About"]
    )

# Main content
if page == "Dashboard":
    st.header("📊 Financial Dashboard")
    
    df = get_dataframe()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        balance = calculate_balance()
        st.metric("💵 Balance", f"${balance:,.2f}")
    
    with col2:
        if not df.empty:
            income = df[df['type'] == 'Income']['amount'].sum()
        else:
            income = 0
        st.metric("📈 Income", f"${income:,.2f}")
    
    with col3:
        if not df.empty:
            expenses = df[df['type'] == 'Expense']['amount'].sum()
        else:
            expenses = 0
        st.metric("📉 Expenses", f"${expenses:,.2f}")
    
    with col4:
        if not df.empty:
            avg_transaction = df['amount'].mean()
        else:
            avg_transaction = 0
        st.metric("📊 Avg", f"${avg_transaction:,.2f}")
    
    # Budget alerts
    alerts = check_budget_alerts(df)
    if alerts:
        st.warning("⚠️ Budget Alerts")
        for alert in alerts:
            st.write(f"**{alert['category']}**: ${alert['spent']:.2f} / ${alert['budget']:.2f} (Over by ${alert['over']:.2f})")
    
    st.divider()
    
    # Summary charts and tables
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Spending by Category")
            expense_df = df[df['type'] == 'Expense']
            if not expense_df.empty:
                category_spending = expense_df.groupby('category')['amount'].sum().reset_index()
                category_spending.columns = ['Category', 'Amount']
                category_spending = category_spending.sort_values('Amount', ascending=False)
                st.bar_chart(category_spending.set_index('Category'))
        
        with col2:
            st.subheader("Income vs Expenses")
            daily_summary = df.groupby('type')['amount'].sum().reset_index()
            daily_summary.columns = ['Type', 'Total']
            st.bar_chart(daily_summary.set_index('Type'))
        
        # Recent transactions
        st.subheader("🔄 Recent Transactions")
        recent = df.sort_values('date', ascending=False).head(8)
        st.dataframe(recent[['date', 'category', 'amount', 'type', 'description']], 
                    use_container_width=True, hide_index=True)
    else:
        st.info("👈 Add your first transaction in the 'Add Transaction' page!")

elif page == "Add Transaction":
    st.header("➕ Add New Transaction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_type = st.radio("Transaction Type", ["Income", "Expense"])
        
        if transaction_type == "Income":
            categories = ["Salary", "Freelance", "Investment", "Bonus", "Gift", "Refund", "Other"]
        else:
            categories = ["Food", "Transportation", "Entertainment", "Bills", "Shopping", 
                         "Health", "Education", "Utilities", "Insurance", "Other"]
        
        category = st.selectbox("Category", categories)
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
    
    with col2:
        date = st.date_input("Date", datetime.now())
        description = st.text_input("Description")
        tags_input = st.text_input("Tags (comma-separated, optional)")
        tags = [t.strip() for t in tags_input.split(',')] if tags_input else []
    
    if st.button("✅ Add Transaction", type="primary", use_container_width=True):
        add_transaction(date, category, amount, transaction_type, description, tags)
        st.success(f"✅ Added {transaction_type}: ${amount:.2f} - {category}")
        st.rerun()

elif page == "Budgets":
    st.header("💳 Budget Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Set New Budget")
        budget_category = st.selectbox("Category", 
            ["Food", "Transportation", "Entertainment", "Shopping", "Health", "Education", "Utilities", "Other"])
        budget_month = st.date_input("Month", datetime.now()).strftime('%Y-%m')
        budget_amount = st.number_input("Budget Amount ($)", min_value=0.01, step=0.01)
        
        if st.button("➕ Set Budget", use_container_width=True):
            add_budget(budget_category, budget_amount, budget_month)
            st.success(f"✅ Budget set: ${budget_amount:.2f} for {budget_category}")
            st.rerun()
    
    with col2:
        st.subheader("📊 Budget Overview")
        if st.session_state.budgets:
            df = get_dataframe()
            budget_data = []
            
            for budget_key, budget_amount in st.session_state.budgets.items():
                category = budget_key.split('_')[0]
                spending = get_spending_by_category(df).get(category, 0)
                remaining = budget_amount - spending
                percentage = (spending / budget_amount * 100) if budget_amount > 0 else 0
                
                budget_data.append({
                    'Category': category,
                    'Budget': f"${budget_amount:.2f}",
                    'Spent': f"${spending:.2f}",
                    'Remaining': f"${remaining:.2f}",
                    'Usage %': f"{percentage:.1f}%"
                })
            
            if budget_data:
                st.dataframe(budget_data, use_container_width=True, hide_index=True)
        else:
            st.info("No budgets set yet")

elif page == "Goals":
    st.header("🎯 Savings Goals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create New Goal")
        goal_name = st.text_input("Goal Name (e.g., Vacation, Car)")
        target_amount = st.number_input("Target Amount ($)", min_value=0.01, step=0.01)
        goal_deadline = st.date_input("Target Deadline")
        goal_category = st.selectbox("Category", 
            ["Vacation", "Education", "Home", "Vehicle", "Investment", "Emergency", "Other"])
        
        if st.button("➕ Create Goal", use_container_width=True):
            add_goal(goal_name, target_amount, goal_deadline, goal_category)
            st.success(f"✅ Goal created: {goal_name}")
            st.rerun()
    
    with col2:
        st.subheader("📈 Goals Progress")
        if st.session_state.goals:
            df = get_dataframe()
            
            for idx, goal in enumerate(st.session_state.goals):
                goal_category_spending = get_spending_by_category(df).get(goal['category'], 0)
                progress_pct = (goal_category_spending / goal['target'] * 100) if goal['target'] > 0 else 0
                days_left = (datetime.strptime(goal['deadline'], '%Y-%m-%d') - datetime.now()).days
                
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{goal['name']}**")
                    st.progress(min(progress_pct / 100, 1.0))
                    st.caption(f"${goal_category_spending:.2f} / ${goal['target']:.2f} ({progress_pct:.1f}%) • {days_left} days left")
                
                with col_b:
                    if st.button("❌", key=f"delete_goal_{idx}"):
                        st.session_state.goals.pop(idx)
                        st.rerun()
        else:
            st.info("No goals set yet")

elif page == "Recurring":
    st.header("🔄 Recurring Transactions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add Recurring Transaction")
        rec_type = st.radio("Type", ["Income", "Expense"], key="rec_type")
        rec_category = st.selectbox("Category", 
            ["Salary", "Rent", "Insurance", "Subscription", "Utility", "Other"])
        rec_amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, key="rec_amount")
        rec_frequency = st.selectbox("Frequency", ["Monthly", "Weekly", "Bi-weekly", "Quarterly", "Annually"])
        
        if st.button("➕ Add Recurring", use_container_width=True):
            add_recurring(rec_category, rec_amount, rec_frequency, rec_type)
            st.success("✅ Recurring transaction added")
            st.rerun()
    
    with col2:
        st.subheader("📋 Active Recurring Transactions")
        if st.session_state.recurring:
            for idx, rec in enumerate(st.session_state.recurring):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{rec['category']}** • {rec['frequency']}")
                    st.caption(f"{rec['type']} - ${rec['amount']:.2f}")
                with col_b:
                    if st.button("❌", key=f"delete_rec_{idx}"):
                        st.session_state.recurring.pop(idx)
                        st.rerun()
        else:
            st.info("No recurring transactions set")

elif page == "Analytics":
    st.header("📈 Advanced Analytics")
    
    df = get_dataframe()
    
    if not df.empty:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", df['date'].min().date())
        with col2:
            end_date = st.date_input("End Date", df['date'].max().date())
        
        mask = (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
        range_df = df[mask]
        
        if not range_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_spent = range_df[range_df['type'] == 'Expense']['amount'].sum()
                st.metric("Total Spent", f"${total_spent:,.2f}")
            with col2:
                total_earned = range_df[range_df['type'] == 'Income']['amount'].sum()
                st.metric("Total Earned", f"${total_earned:,.2f}")
            with col3:
                net = total_earned - total_spent
                st.metric("Net", f"${net:,.2f}")
            
            st.divider()
            
            # Monthly trends chart
            st.subheader("Monthly Trends")
            range_df_copy = range_df.copy()
            range_df_copy['month'] = range_df_copy['date'].dt.to_period('M').astype(str)
            monthly = range_df_copy.groupby(['month', 'type'])['amount'].sum().reset_index()
            
            if not monthly.empty:
                monthly_pivot = monthly.pivot(index='month', columns='type', values='amount').fillna(0)
                st.line_chart(monthly_pivot)
            
            # Top categories chart
            st.subheader("Top Spending Categories")
            expense_df = range_df[range_df['type'] == 'Expense']
            if not expense_df.empty:
                top_cat = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5)
                st.bar_chart(top_cat)
    else:
        st.info("No transactions to analyze")

elif page == "Insights":
    st.header("💡 Smart Insights & Statistics")
    
    df = get_dataframe()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Category Breakdown")
            stats = calculate_category_stats(df)
            
            insight_data = []
            for cat, stat in stats.items():
                insight_data.append({
                    'Category': cat,
                    'Count': stat['count'],
                    'Total': f"${stat['total']:.2f}",
                    'Average': f"${stat['average']:.2f}",
                    'Max': f"${stat['max']:.2f}"
                })
            
            st.dataframe(insight_data, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("Spending Patterns by Day")
            df['day_of_week'] = df['date'].dt.day_name()
            dow_spending = df[df['type'] == 'Expense'].groupby('day_of_week')['amount'].sum().reset_index()
            dow_spending.columns = ['Day', 'Amount']
            st.bar_chart(dow_spending.set_index('Day'))
        
        st.divider()
        
        # Top transactions
        st.subheader("🔝 Top 10 Transactions")
        top_trans = get_top_transactions(df, 10)
        st.dataframe(top_trans, use_container_width=True, hide_index=True)
    else:
        st.info("Add transactions to view insights")

elif page == "About":
    st.header("ℹ️ About Advanced Finance Tracker")
    
    st.markdown("""
    ### 🚀 Advanced Features
    
    #### Core Functionality
    - ✅ **Transaction Management**: Add, track, and organize income/expenses with tags
    - ✅ **Budget Tracking**: Set budgets by category with real-time alerts
    - ✅ **Savings Goals**: Create and monitor progress toward financial goals
    - ✅ **Recurring Transactions**: Automate regular income/expense entries
    - ✅ **Advanced Analytics**: Detailed insights and spending patterns
    - ✅ **Smart Alerts**: Budget overflow warnings and financial notifications
    
    #### Python Concepts Covered
    - **Data Structures**: Lists, dictionaries, sets for data management
    - **Session State**: Persistent data across app reruns
    - **Pandas**: DataFrame operations and aggregations
    - **Datetime**: Complex date filtering and period grouping
    - **JSON**: Data serialization
    - **Functions**: Modular, reusable code
    - **Object-Oriented Design**: Better code organization
    
    #### Streamlit Concepts
    - Multi-page navigation
    - Advanced widgets and layouts
    - Dynamic data display
    - State management
    - User input validation
    - Performance optimization
    
    ### 📚 Learning Outcomes
    Students will master:
    1. Building production-grade web applications
    2. Complex data analysis and visualization
    3. Real-world application design patterns
    4. User experience considerations
    5. Advanced Python programming
    
    ### 🎯 Project Extensions
    **Beginner**: 
    - Add data export to CSV
    - Create custom themes
    - Add expense categories
    
    **Intermediate**:
    - Database integration (SQLite)
    - User authentication
    - Data backup system
    
    **Advanced**:
    - REST API backend
    - Machine learning predictions
    - Mobile app companion
    - Real bank integration
    
    ### 💾 Data Persistence
    Current: Session-based (in-memory)
    
    Potential upgrades:
    - SQLite database
    - PostgreSQL backend
    - Cloud storage (Firebase)
    - CSV import/export
    
    ---
    **Version**: 2.1 Advanced (Simplified)
    **Last Updated**: 2025
    **Difficulty**: Intermediate to Advanced
    """)

# Footer
st.divider()
st.caption(f"Advanced Finance Tracker v2.1 • Built with Streamlit • {len(st.session_state.transactions)} transactions tracked")
