import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Inventory Auditor Pro")

st.title("📦 Inventory Cash Release Auditor")

# --- 1. Sidebar Parameters ---
with st.sidebar:
    st.header("Financial Parameters")
    unit_cost = st.number_input("Cost per Unit ($)", min_value=0.01, value=10.0)
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
            is_date = False
            try:
                if not str(first_val).isdigit():
                    raw_df['Day'] = pd.to_datetime(raw_df['Day'])
                    is_date = True
            except:
                is_date = False

            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Reindex and Forward Fill
            if is_date:
                full_range = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            else:
                full_range = range(int(raw_df.index.min()), int(raw_df.index.max()) + 1)
            
            df = raw_df.reindex(full_range)
            df['Closing Balance'] = df['Closing Balance'].ffill()
            df = df.reset_index().rename(columns={'index': 'Day'})

            # --- 3. Evaluations ---
            min_inv = df['Closing Balance'].min()
            avg_inv = df['Closing Balance'].mean()
            annual_holding_cost = (avg_inv * unit_cost) * holding_cost_pct

            # Calculate Reduced Data
            total_red = reduction_qty + (min_inv * reduction_pct)
            df['Proposed Balance'] = (df['Closing Balance'] - total_red).clip(lower=0)
            
            new_avg_inv = df['Proposed Balance'].mean()
            new_holding_cost = (new_avg_inv * unit_cost) * holding_cost_pct
            cash_released = total_red * unit_cost
            annual_savings = annual_holding_cost - new_holding_cost
            daily_savings = annual_savings / 365
            turn_multiplier = (avg_inv / new_avg_inv) if new_avg_inv > 0 else 1.0

            # --- 4. Metrics Display ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Min Inventory Level", f"{min_inv:,.0f} units")
            m2.metric("Avg Inventory Level", f"{avg_inv:,.0f} units")
            m3.metric("Annual Holding Cost", f"${annual_holding_cost:,.2f}")

            # --- 5. Comparison Plot ---
            st.subheader("Inventory Trend: Current vs. Proposed")
            
            fig = go.Figure()

            # Current State Trace
            fig.add_trace(go.Scatter(
                x=df['Day'], y=df['Closing Balance'],
                mode='lines', name='Current Inventory',
                line=dict(width=2, color='#636EFA'),
                fill='tozeroy'
            ))

            # Proposed State Trace
            fig.add_trace(go.Scatter(
                x=df['Day'], y=df['Proposed Balance'],
                mode='lines', name='Proposed (Reduced) Inventory',
                line=dict(width=2, color='#EF553B', dash='dot'),
                fill='tonexty' # Highlights the gap/saving area
            ))

            # Add Minimum Inventory Line
            fig.add_hline(y=min_inv, line_dash="dash", line_color="green", 
                          annotation_text=f"Current Min: {min_inv}", annotation_position="bottom right")

            fig.update_layout(
                xaxis_title="Day" if not is_date else "Date",
                yaxis_title="Units",
                hovermode="x unified",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 6. Impact Results ---
            st.divider()
            st.subheader("💰 Cash Release & Impact Analysis")
            res1, res2, res3 = st.columns(3)
            with res1:
                st.info(f"**Cash Released**\n\n# ${cash_released:,.2f}")
            with res2:
                st.success(f"**Annual Savings**\n\n# ${annual_savings:,.2f}")
                st.write(f"Daily Savings: **${daily_savings:,.2f}**")
            with res3:
                st.warning(f"**Efficiency Gain**\n\n# {turn_multiplier:.2f}x")
                st.write("Increase in Inventory Turns")

        else:
            st.error("Missing required columns: 'Day' and 'Closing Balance'.")
    except Exception as e:
        st.error(f"Error: {e}")
