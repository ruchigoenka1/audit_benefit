import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration & Custom Styling
st.set_page_config(layout="wide", page_title="AI Inventory Auditor Pro", page_icon="📦")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; }
    div[data-testid="stMetricDelta"] { font-size: 16px; }
    .stContainer { border: 1px solid #30363d !important; border-radius: 10px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Header
st.title("📦 AI Inventory Auditor Pro")
st.markdown("### Structural Inventory Audit & Cash Release Simulation")
st.divider()

# 3. Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    with st.expander("Cost Settings", expanded=True):
        unit_cost = st.number_input("Unit Cost (₹)", min_value=1.0, value=100.0, step=10.0)
        holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=18.0, step=0.5) / 100
        ordering_cost = st.number_input("Ordering Cost (₹)", min_value=0.0, value=500.0)

    st.header("🎯 What-If Targets")
    st.info("Simulate reducing stock levels from the current floor (Minimum Inventory).")
    red_qty = st.number_input("Cut Fixed Units", min_value=0.0, value=0.0, step=10.0)
    red_pct = st.number_input("Cut % from Min", min_value=0.0, max_value=100.0, value=10.0, step=1.0) / 100

# 4. Data Engine
uploaded_file = st.file_uploader("Upload Inventory XLSX (Columns: Day, Closing Balance)", type=["xlsx"])

if uploaded_file:
    try:
        raw_df = pd.read_excel(uploaded_file)
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            # Smart Logic: Identify if X-axis is Dates or integers
            first_val = raw_df['Day'].iloc[0]
            is_date = not str(first_val).isdigit()
            if is_date:
                raw_df['Day'] = pd.to_datetime(raw_df['Day'])

            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Fill Gaps using Forward Fill (Realistic for inventory)
            if is_date:
                full_range = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            else:
                full_range = range(int(raw_df.index.min()), int(raw_df.index.max()) + 1)
            
            df = raw_df.reindex(full_range).ffill().reset_index().rename(columns={'index': 'Day'})

            # --- 5. Calculation Engine ---
            min_inv = df['Closing Balance'].min()
            max_inv = df['Closing Balance'].max()
            hist_avg_inv = df['Closing Balance'].mean()
            hist_holding_total = (hist_avg_inv * unit_cost) * holding_cost_pct

            # New Scenario
            reduction_target = red_qty + (min_inv * red_pct)
            df['Proposed'] = (df['Closing Balance'] - reduction_target).clip(lower=0)
            
            prop_avg_inv = df['Proposed'].mean()
            prop_holding_total = (prop_avg_inv * unit_cost) * holding_cost_pct
            
            # KPI Deltas
            cash_released = reduction_target * unit_cost
            annual_savings = hist_holding_total - prop_holding_total
            turn_improvement = (hist_avg_inv / prop_avg_inv) if prop_avg_inv > 0 else 1.0

            # --- 6. Visual Dashboard ---
            # Top Row: Benchmarks
            st.subheader("📊 Baseline Benchmarks (Historical)")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Min Inventory", f"{min_inv:,.0f} U")
            b2.metric("Max Inventory", f"{max_inv:,.0f} U")
            b3.metric("Avg Inventory", f"{hist_avg_inv:,.0f} U")
            b4.metric("Avg Value", f"₹{hist_avg_inv * unit_cost:,.0f}")

            # Plotting
            st.subheader("📈 Inventory Level Comparison")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Closing Balance'], name='Historical', line=dict(color='#00d4ff', width=2), fill='tozeroy'))
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Proposed'], name='Optimized', line=dict(color='#ff4b4b', width=2, dash='dot'), fill='tonexty'))
            fig.add_hline(y=min_inv, line_dash="dash", line_color="#2ecc71", annotation_text="Safety Floor")
            fig.update_layout(template="plotly_dark", hovermode="x unified", height=500, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # --- 7. Strategic Impact Row ---
            st.divider()
            st.subheader("💡 Strategic Impact Report")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                with st.container(border=True):
                    st.write("**LIQUIDITY GAIN**")
                    st.metric("Immediate Cash Released", f"₹{cash_released:,.2f}", delta="Instant ROI")
                    st.write(f"Old Value: ₹{hist_avg_inv * unit_cost:,.0f}")
                    st.write(f"New Value: ₹{prop_avg_inv * unit_cost:,.0f}")

            with c2:
                with st.container(border=True):
                    st.write("**COST REDUCTION**")
                    st.metric("Annual Holding Saving", f"₹{annual_savings:,.2f}", delta=f"₹{annual_savings/365:,.2f} / day")
                    st.write(f"Old Cost: ₹{hist_holding_total:,.2f}")
                    st.write(f"New Cost: ₹{prop_holding_total:,.2f}")

            with c3:
                with st.container(border=True):
                    st.write("**EFFICIENCY MULTIPLIER**")
                    st.metric("Inventory Turns", f"{turn_improvement:.2f}x", delta=f"{(turn_improvement-1)*100:.1f}% Leaner")
                    st.write("Base Index: 1.00x")
                    st.write(f"New Efficiency: {turn_improvement:.2f}x")

            # Data Preview
            with st.expander("🔍 Audit Trail (Data Table)"):
                st.dataframe(df.style.format({"Closing Balance": "{:,.0f}", "Proposed": "{:,.0f}"}), use_container_width=True)

        else:
            st.error("Error: The file must contain 'Day' and 'Closing Balance' columns.")
    except Exception as e:
        st.error(f"Processing Error: {e}")
else:
    st.info("Please upload an inventory Excel file to generate the structural audit.")
