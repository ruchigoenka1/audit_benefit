import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="AI Inventory Auditor Pro", page_icon="📦")

# Custom CSS for better UI and Rupee visibility
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] { font-size: 32px; color: #00d4ff; }
    .stContainer { border: 1px solid #30363d !important; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Mutual Exclusion Logic (Sidebar) ---
def update_fixed():
    st.session_state.pct_input = 0.0

def update_pct():
    st.session_state.fixed_input = 0.0

if 'fixed_input' not in st.session_state:
    st.session_state.fixed_input = 0.0
if 'pct_input' not in st.session_state:
    st.session_state.pct_input = 0.0

# --- 3. Sidebar Configuration ---
with st.sidebar:
    st.title("⚙️ Parameters")
    with st.expander("Financial Setup", expanded=True):
        unit_cost = st.number_input("Unit Cost (₹)", min_value=1.0, value=100.0)
        holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=18.0) / 100
        ordering_cost = st.number_input("Ordering Cost (₹)", min_value=0.0, value=500.0)

    st.divider()
    st.subheader("🎯 Optimization Targets")
    st.info("Adjusting one resets the other to zero.")
    
    red_qty = st.number_input(
        "Cut Fixed Units", 
        min_value=0.0, 
        key="fixed_input", 
        on_change=update_fixed
    )

    red_pct_val = st.number_input(
        "Cut % from Min", 
        min_value=0.0, 
        max_value=100.0, 
        key="pct_input", 
        on_change=update_pct
    )
    red_pct = red_pct_val / 100

# --- 4. Main Body ---
st.title("📦 AI Inventory Auditor Pro")
uploaded_file = st.file_uploader("Upload Inventory Excel File (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        raw_df = pd.read_excel(uploaded_file)
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            # Smart Axis: Dates vs. Day Numbers
            first_val = raw_df['Day'].iloc[0]
            is_date = not str(first_val).isdigit()
            if is_date:
                raw_df['Day'] = pd.to_datetime(raw_df['Day'])

            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Reindex and Forward Fill (Realistic Inventory Logic)
            if is_date:
                full_range = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            else:
                full_range = range(int(raw_df.index.min()), int(raw_df.index.max()) + 1)
            
            df = raw_df.reindex(full_range).ffill().reset_index().rename(columns={'index': 'Day'})

            # --- 5. Calculation Engine ---
            min_inv = df['Closing Balance'].min()
            hist_avg_inv = df['Closing Balance'].mean()
            hist_holding_cost = (hist_avg_inv * unit_cost) * holding_cost_pct

            # Determine Reduction
            reduction_target = red_qty if red_qty > 0 else (min_inv * red_pct)
            df['Proposed'] = (df['Closing Balance'] - reduction_target).clip(lower=0)
            
            prop_avg_inv = df['Proposed'].mean()
            prop_holding_cost = (prop_avg_inv * unit_cost) * holding_cost_pct
            
            # Impact Analytics
            cash_released = reduction_target * unit_cost
            annual_savings = hist_holding_cost - prop_holding_cost
            turn_improvement = (hist_avg_inv / prop_avg_inv) if prop_avg_inv > 0 else 1.0

            # --- 6. Visual Presentation ---
            st.subheader("📈 Inventory Trend: Historical vs. Proposed")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Closing Balance'], name='Historical', line=dict(color='#00d4ff'), fill='tozeroy'))
            fig.add_trace(go.Scatter(x=df['Day'], y=df['Proposed'], name='Optimized', line=dict(color='#ff4b4b', dash='dot'), fill='tonexty'))
            fig.add_hline(y=min_inv, line_dash="dash", line_color="#2ecc71", annotation_text=f"Current Min: {min_inv}")
            fig.update_layout(template="plotly_dark", height=450, xaxis_title="Timeline", yaxis_title="Units")
            st.plotly_chart(fig, use_container_width=True)

            # --- 7. Strategic Impact Report ---
            st.divider()
            st.subheader("💰 Cash Release & Impact Analysis")
            
            col1, col2, col3 = st.columns(3)

            with col1:
                with st.container(border=True):
                    st.write("**INVENTORY INVESTMENT**")
                    st.metric("Cash Released", f"₹{cash_released:,.2f}")
                    st.write(f"Historical Value: ₹{hist_avg_inv * unit_cost:,.0f}")
                    st.write(f"New Scenario: ₹{prop_avg_inv * unit_cost:,.0f}")

            with col2:
                with st.container(border=True):
                    st.write("**ANNUAL HOLDING COST**")
                    st.metric("Annual Saving", f"₹{annual_savings:,.2f}", delta=f"₹{annual_savings/365:,.2f} / day")
                    st.write(f"Historical Cost: ₹{hist_holding_cost:,.2f}")
                    st.write(f"New Scenario: ₹{prop_holding_cost:,.2f}")

            with col3:
                with st.container(border=True):
                    st.write("**EFFICIENCY GAIN**")
                    st.metric("Turn Multiplier", f"{turn_improvement:.2f}x", delta=f"{(turn_improvement-1)*100:.1f}% Increase")
                    st.write("Base Index: 1.00x")
                    st.write(f"Proposed Efficiency: {turn_improvement:.2f}x")

            with st.expander("🔍 View Detailed Audit Table"):
                st.dataframe(df, use_container_width=True)

        else:
            st.error("Missing Columns: Please ensure your file has 'Day' and 'Closing Balance'.")
    except Exception as e:
        st.error(f"Audit Error: {e}")
else:
    st.info("👋 Upload an Excel file to begin the inventory audit.")
