import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Inventory Auditor Pro")

st.title("📦 Inventory Cash Release Auditor")

# --- 1. Sidebar Parameters ---
with st.sidebar:
    st.header("Financial Parameters")
    unit_cost = st.number_input("Cost per Unit (₹)", min_value=0.01, value=10.0)
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=20.0) / 100
    
    st.divider()
    st.header("Optimization Targets")
    reduction_qty = st.number_input("Fixed Unit Reduction", min_value=0.0, value=0.0)
    reduction_pct = st.number_input("Reduction from Min (%)", min_value=0.0, max_value=100.0, value=0.0) / 100

# --- 2. File Upload ---
uploaded_file = st.file_uploader("Upload Inventory Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        raw_df = pd.read_excel(uploaded_file)
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            # Smart Axis Logic
            first_val = raw_df['Day'].iloc[0]
            is_date = not str(first_val).isdigit()
            if is_date:
                raw_df['Day'] = pd.to_datetime(raw_df['Day'])

            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Reindex and Forward Fill
            if is_date:
                full_range = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            else:
                full_range = range(int(raw_df.index.min()), int(raw_df.index.max()) + 1)
            
            df = raw_df.reindex(full_range)
            df['Closing Balance'] = df['Closing Balance'].ffill()
            df = df.reset_index().rename(columns={'index': 'Day'})

            # --- 3. Evaluations (Historical vs Proposed) ---
            min_inv = df['Closing Balance'].min()
            
            # Historical Stats
            hist_avg_inv = df['Closing Balance'].mean()
            hist_holding_cost = (hist_avg_inv * unit_cost) * holding_cost_pct
            
            # Proposed Stats
            total_red_units = reduction_qty + (min_inv * reduction_pct)
            df['Proposed Balance'] = (df['Closing Balance'] - total_red_units).clip(lower=0)
            
            prop_avg_inv = df['Proposed Balance'].mean()
            prop_holding_cost = (prop_avg_inv * unit_cost) * holding_cost_pct
            
            # Impact Metrics
            cash_released = total_red_units * unit_cost
            annual_savings = hist_holding_cost - prop_holding_cost
            
            # Efficiency (Turns) - using 1.0 as base for comparison
            hist_turn = 1.0 
            prop_turn = (hist_avg_inv / prop_avg_inv) if prop_avg_inv > 0 else 1.0

            # --- 4. Comparison Plot ---
            st.subheader("Inventory Trend: Current vs. Proposed")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Closing Balance'], mode='lines', name='Historical', line=dict(color='#636EFA'), fill='tozeroy'))
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Proposed Balance'], mode='lines', name='Proposed', line=dict(color='#EF553B', dash='dot'), fill='tonexty'))
            fig.add_hline(y=min_inv, line_dash="dash", line_color="green", annotation_text=f"Min: {min_inv}")
            fig.update_layout(xaxis_title="Timeline", yaxis_title="Units", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            # --- 5. Enhanced KPI Analysis (Historical | Proposed | Saving) ---
            st.divider()
            st.subheader("💰 Cash Release & Impact Analysis")
            
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Inventory Investment**")
                st.metric("Cash Released", f"₹{cash_released:,.2f}", delta="Instant Liquid Cash", delta_color="normal")
                st.caption(f"Historical Value: ₹{hist_avg_inv * unit_cost:,.0f}")
                st.caption(f"New Scenario Value: ₹{prop_avg_inv * unit_cost:,.0f}")

            with col2:
                st.write("**Annual Holding Cost**")
                st.metric("Total Saving", f"₹{annual_savings:,.2f}", delta=f"₹{annual_savings/365:,.2f} / day")
                st.caption(f"Historical Cost: ₹{hist_holding_cost:,.2f}")
                st.caption(f"New Scenario Cost: ₹{prop_holding_cost:,.2f}")

            with col3:
                st.write("**Efficiency (Inventory Turns)**")
                st.metric("Turn Improvement", f"{prop_turn:.2f}x", delta=f"{(prop_turn - 1)*100:.1f}% Increase")
                st.caption(f"Historical Turns: {hist_turn:.2f}x")
                st.caption(f"New Scenario Turns: {prop_turn:.2f}x")

        else:
            st.error("Please ensure columns are 'Day' and 'Closing Balance'.")
    except Exception as e:
        st.error(f"Error: {e}")
