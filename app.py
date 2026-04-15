import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Inventory Auditor Pro")

st.title("📦 Inventory Cash Release Auditor")

# --- 1. Sidebar Parameters ---
with st.sidebar:
    st.header("Financial Parameters")
    unit_cost = st.number_input("Cost per Unit ($)", min_value=0.01, value=10.0)
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=20.0) / 100
    
    st.divider()
    st.header("Optimization Targets")
    # User inputs for reduction simulation
    reduction_qty = st.number_input("Reduction Amount (Units)", min_value=0.0, value=0.0)
    reduction_pct = st.number_input("Reduction from Min (%)", min_value=0.0, max_value=100.0, value=0.0) / 100

# --- 2. File Upload ---
uploaded_file = st.file_uploader("Upload Inventory CSV (Columns: Day, Closing Balance)", type=["csv"])

if uploaded_file is not None:
    # Read and clean data
    raw_df = pd.read_csv(uploaded_file)
    
    # Standardize column names to handle potential casing issues
    raw_df.columns = [c.strip().title() for c in raw_df.columns]
    
    if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
        # Convert Day to Datetime
        raw_df['Day'] = pd.to_datetime(raw_df['Day'])
        raw_df = raw_df.sort_values('Day').set_index('Day')
        
        # Fill missing dates
        all_days = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
        df = raw_df.reindex(all_days)
        
        # Interpolate missing balances
        df['Closing Balance'] = df['Closing Balance'].interpolate(method='linear')
        df = df.reset_index().rename(columns={'index': 'Day'})

        # --- 3. Core Evaluations ---
        min_inv = df['Closing Balance'].min()
        avg_inv = df['Closing Balance'].mean()
        
        # Financials
        total_value = avg_inv * unit_cost
        annual_holding_cost = total_value * holding_cost_pct
        
        # Metrics Display
        m1, m2, m3 = st.columns(3)
        m1.metric("Minimum Inventory Level", f"{min_inv:,.0f} units")
        m2.metric("Average Inventory Level", f"{avg_inv:,.0f} units")
        m3.metric("Annual Holding Cost", f"${annual_holding_cost:,.2f}")

        # --- 4. Plotting ---
        fig = px.area(df, x='Day', y='Closing Balance', title="Inventory Level Trend", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)

        # --- 5. Cash Release & What-If Analysis ---
        st.subheader("💰 Cash Release & Impact Analysis")
        
        # Calculate reduction based on user inputs
        # We calculate reduction from the MINIMUM inventory level as requested
        total_reduction_units = reduction_qty + (min_inv * reduction_pct)
        
        # Results calculation
        cash_released = total_reduction_units * unit_cost
        new_avg_inv = max(0, avg_inv - total_reduction_units)
        new_holding_cost = (new_avg_inv * unit_cost) * holding_cost_pct
        annual_savings = annual_holding_cost - new_holding_cost
        daily_savings = annual_savings / 365
        
        # Turnover change (Efficiency)
        # Using a theoretical 'Inventory Turn' ratio (COGS / Avg Inventory)
        # Assuming COGS is constant, the ratio change is proportional to the average inventory change
        turn_multiplier = (avg_inv / new_avg_inv) if new_avg_inv > 0 else 1.0

        # Display Impact Results
        res1, res2, res3 = st.columns(3)
        with res1:
            st.info(f"**Total Cash Released**\n\n# ${cash_released:,.2f}")
        with res2:
            st.success(f"**Annual Holding Savings**\n\n# ${annual_savings:,.2f}")
            st.write(f"Daily Cost Saving: **${daily_savings:,.2f}**")
        with res3:
            st.warning(f"**Efficiency Gain**\n\n# {turn_multiplier:.2f}x")
            st.write("Increase in Inventory Turns")

    else:
        st.error("CSV must contain 'Day' and 'Closing Balance' columns.")
else:
    st.info("Waiting for CSV file upload...")
