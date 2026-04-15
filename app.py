import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Inventory Cash Release Tool")

st.title("📦 Inventory Auditor & Cash Release Calculator")

# --- 1. Sidebar Inputs ---
with st.sidebar:
    st.header("Cost Parameters")
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=20.0) / 100
    ordering_cost = st.number_input("Ordering Cost ($)", min_value=0.0, value=50.0)
    
    st.divider()
    st.header("Cash Release Simulation")
    reduction_value = st.number_input("Reduction from Min Inventory (Units)", min_value=0.0, value=0.0)
    unit_cost = st.number_input("Cost per Unit ($)", min_value=0.1, value=10.0)

# --- 2. Data Input Section ---
st.subheader("1. Data Entry")
col1, col2 = st.columns([1, 2])

with col1:
    input_data = st.data_editor(
        pd.DataFrame([
            {"Date": pd.Timestamp.now().date(), "Closing Balance": 100},
            {"Date": (pd.Timestamp.now() + pd.Timedelta(days=5)).date(), "Closing Balance": 150}
        ]),
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )

if not input_data.empty:
    # Process the Dataframe
    df = input_data.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    
    # Reindex to fill missing days
    all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(all_days)
    
    # Interpolate missing balances (Linear is usually best for trend analysis)
    df['Closing Balance'] = df['Closing Balance'].interpolate(method='linear')
    df = df.reset_index().rename(columns={'index': 'Date'})

    # --- 3. Evaluations ---
    min_inv = df['Closing Balance'].min()
    avg_inv = df['Closing Balance'].mean()
    total_value = avg_inv * unit_cost
    annual_holding_cost = total_value * holding_cost_pct
    
    # Calculate Turns (Assuming simplified COGS = Avg Inv * 4 for example, 
    # but usually requires Sales data. Here we'll use a placeholder ratio.)
    inventory_turns = 10 # Placeholder baseline

    # --- 4. Metrics Display ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Min Inventory Level", f"{min_inv:,.0f} units")
    m2.metric("Avg Inventory Level", f"{avg_inv:,.0f} units")
    m3.metric("Annual Holding Cost", f"${annual_holding_cost:,.2f}")

    # --- 5. Plotting ---
    st.subheader("Inventory Level Over Time")
    fig = px.line(df, x='Date', y='Closing Balance', title="Daily Inventory Balance")
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. What-If Analysis (Cash Release) ---
    st.divider()
    st.subheader("2. Optimization Impact")
    
    # Logic: Reducing Min Inventory reduces the entire baseline (Avg Inventory)
    new_avg_inv = avg_inv - reduction_value
    cash_released = reduction_value * unit_cost
    new_holding_cost = (new_avg_inv * unit_cost) * holding_cost_pct
    annual_savings = annual_holding_cost - new_holding_cost
    daily_savings = annual_savings / 365
    
    # Impact Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cash Released", f"${cash_released:,.2f}", delta="Instant Liquid Cash", delta_color="normal")
    c2.metric("New Annual Holding Cost", f"${new_holding_cost:,.2f}")
    c3.metric("Daily Cost Saving", f"${daily_savings:,.2f}", delta="OpEx Reduction")
    
    # Turnover calculation (Simplified: Turns increase as Avg Inv decreases)
    turn_improvement = (avg_inv / new_avg_inv) if new_avg_inv > 0 else 0
    c4.metric("Inventory Turn Multiplier", f"{turn_improvement:.2fx}", delta="Efficiency Gain")

else:
    st.info("Please enter data in the table above to see analysis.")
