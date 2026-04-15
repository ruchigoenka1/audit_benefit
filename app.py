import streamlit as st
import pandas as pd
import plotly.express as px

# Set page layout to wide for better dashboard visibility
st.set_page_config(layout="wide", page_title="Inventory Auditor Pro")

st.title("📦 Inventory Cash Release Auditor")
st.markdown("Analyze inventory gaps, evaluate holding costs, and simulate cash release scenarios.")

# --- 1. Sidebar Parameters ---
with st.sidebar:
    st.header("Financial Parameters")
    unit_cost = st.number_input("Cost per Unit ($)", min_value=0.01, value=10.0, step=1.0)
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=20.0, step=0.5) / 100
    ordering_cost = st.number_input("Ordering Cost ($)", min_value=0.0, value=50.0, step=5.0)
    
    st.divider()
    st.header("Optimization Targets")
    st.write("Simulate cutting inventory levels from the Minimum point:")
    reduction_qty = st.number_input("Fixed Unit Reduction", min_value=0.0, value=0.0)
    reduction_pct = st.number_input("Percentage Reduction from Min (%)", min_value=0.0, max_value=100.0, value=0.0) / 100

# --- 2. File Upload (XLSX) ---
uploaded_file = st.file_uploader("Upload Inventory Excel File", type=["xlsx"])

if uploaded_file is not None:
    # Read Excel
    try:
        raw_df = pd.read_excel(uploaded_file)
        
        # Standardize column names (strips spaces and fixes casing)
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        # Check if required columns exist
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            
            # Data Cleaning & Interpolation
            raw_df['Day'] = pd.to_datetime(raw_df['Day'])
            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Reindex to fill missing days in the calendar sequence
            all_days = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            df = raw_df.reindex(all_days)
            
            # Fill missing inventory values using linear interpolation
            df['Closing Balance'] = df['Closing Balance'].interpolate(method='linear')
            df = df.reset_index().rename(columns={'index': 'Day'})

            # --- 3. Core Evaluations ---
            min_inv = df['Closing Balance'].min()
            avg_inv = df['Closing Balance'].mean()
            annual_holding_cost = (avg_inv * unit_cost) * holding_cost_pct
            
            # Metrics Display
            st.subheader("Current Performance Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("Min Inventory Level", f"{min_inv:,.0f} units")
            m2.metric("Avg Inventory Level", f"{avg_inv:,.0f} units")
            m3.metric("Annual Holding Cost", f"${annual_holding_cost:,.2f}")

            # --- 4. Plotting ---
            fig = px.area(df, x='Day', y='Closing Balance', 
                          title="Daily Inventory Balance (Interpolated)", 
                          color_discrete_sequence=['#00CC96'],
                          template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            # --- 5. Cash Release & What-If Analysis ---
            st.divider()
            st.subheader("💰 Cash Release & Impact Simulation")
            
            # Calculate total units to be removed
            # Logic: Reducing a fixed amount AND/OR a percentage of the current floor (Min)
            total_reduction_units = reduction_qty + (min_inv * reduction_pct)
            
            # Safety check: Can't release more than the current average
            total_reduction_units = min(total_reduction_units, avg_inv)
            
            # Impact Calculations
            cash_released = total_reduction_units * unit_cost
            new_avg_inv = avg_inv - total_reduction_units
            new_holding_cost = (new_avg_inv * unit_cost) * holding_cost_pct
            annual_savings = annual_holding_cost - new_holding_cost
            daily_savings = annual_savings / 365
            
            # Efficiency Metric: Inventory Turn Multiplier
            # If avg inventory drops while throughput stays same, turns increase
            turn_multiplier = (avg_inv / new_avg_inv) if new_avg_inv > 0 else 1.0

            # Display Results in clean boxes
            res1, res2, res3 = st.columns(3)
            with res1:
                st.info(f"**Total Cash Released**\n\n# ${cash_released:,.2f}")
                st.caption("Immediate liquidity back to the business.")
            with res2:
                st.success(f"**Annual Holding Savings**\n\n# ${annual_savings:,.2f}")
                st.write(f"Daily Cost Saving: **${daily_savings:,.2f}**")
            with res3:
                st.warning(f"**Efficiency Gain**\n\n# {turn_multiplier:.2f}x")
                st.write("Improvement in Inventory Turn Ratio")

            # Optional: Show the data table
            with st.expander("View Cleaned Data Table"):
                st.dataframe(df, use_container_width=True)

        else:
            st.error("The uploaded file is missing required columns. Please ensure it has 'Day' and 'Closing Balance'.")
            
    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("👋 Welcome! Please upload an Excel file (.xlsx) with 'Day' and 'Closing Balance' columns to see the audit.")
