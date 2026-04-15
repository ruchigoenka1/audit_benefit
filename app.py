import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Inventory Auditor Pro")

st.title("📦 Inventory Cash Release Auditor")

# --- 1. Sidebar ---
with st.sidebar:
    st.header("Financial Parameters")
    unit_cost = st.number_input("Cost per Unit ($)", min_value=0.01, value=10.0)
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", min_value=0.0, value=20.0) / 100
    st.divider()
    st.header("Optimization")
    reduction_qty = st.number_input("Fixed Unit Reduction", min_value=0.0, value=0.0)
    reduction_pct = st.number_input("Reduction from Min (%)", min_value=0.0, max_value=100.0, value=0.0) / 100

# --- 2. File Upload ---
uploaded_file = st.file_uploader("Upload Inventory Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        raw_df = pd.read_excel(uploaded_file)
        
        # Standardize column names
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            
            # --- SMART AXIS LOGIC ---
            # Check if the 'Day' column is numeric or date-like
            first_val = raw_df['Day'].iloc[0]
            
            is_date = False
            try:
                # If it's already a datetime or a string that looks like a date
                if isinstance(first_val, (pd.Timestamp, pd.datetime)) or not str(first_val).isdigit():
                    raw_df['Day'] = pd.to_datetime(raw_df['Day'])
                    is_date = True
            except:
                is_date = False

            # Fill missing sequence
            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            if is_date:
                # Calendar Day Interpolation
                full_range = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            else:
                # Numeric Day Interpolation (1, 2, 3...)
                full_range = range(int(raw_df.index.min()), int(raw_df.index.max()) + 1)
            
            df = raw_df.reindex(full_range)
            df['Closing Balance'] = df['Closing Balance'].interpolate(method='linear')
            df = df.reset_index().rename(columns={'index': 'Day'})

            # --- 3. Evaluations ---
            min_inv = df['Closing Balance'].min()
            avg_inv = df['Closing Balance'].mean()
            annual_holding_cost = (avg_inv * unit_cost) * holding_cost_pct

            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Min Inventory Level", f"{min_inv:,.0f} units")
            m2.metric("Avg Inventory Level", f"{avg_inv:,.0f} units")
            m3.metric("Annual Holding Cost", f"${annual_holding_cost:,.2f}")

            # --- 4. Plotting ---
            xtype = "Date" if is_date else "Day Number"
            fig = px.area(df, x='Day', y='Closing Balance', 
                          title=f"Inventory Trend (X-Axis: {xtype})",
                          labels={'Day': xtype, 'Closing Balance': 'Units'})
            st.plotly_chart(fig, use_container_width=True)

            # --- 5. Cash Release & What-If ---
            st.divider()
            st.subheader("💰 Cash Release & Impact Analysis")
            
            total_red = reduction_qty + (min_inv * reduction_pct)
            total_red = min(total_red, avg_inv) # Cap at average
            
            cash_released = total_red * unit_cost
            new_avg_inv = avg_inv - total_red
            new_holding_cost = (new_avg_inv * unit_cost) * holding_cost_pct
            annual_savings = annual_holding_cost - new_holding_cost
            daily_savings = annual_savings / 365
            turn_multiplier = (avg_inv / new_avg_inv) if new_avg_inv > 0 else 1.0

            res1, res2, res3 = st.columns(3)
            with res1:
                st.info(f"**Cash Released**\n\n# ${cash_released:,.2f}")
            with res2:
                st.success(f"**Annual Savings**\n\n# ${annual_savings:,.2f}")
                st.write(f"Daily: **${daily_savings:,.2f}**")
            with res3:
                st.warning(f"**Efficiency Gain**\n\n# {turn_multiplier:.2f}x")
                st.write("Increase in Turns")

            # Show Dataframe for verification
            with st.expander("Show Processed Data Table"):
                st.dataframe(df, use_container_width=True)

        else:
            st.error(f"Columns 'Day' and 'Closing Balance' not found. Found: {list(raw_df.columns)}")
    except Exception as e:
        st.error(f"Error: {e}")
