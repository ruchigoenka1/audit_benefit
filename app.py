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
        # Load the data
        raw_df = pd.read_excel(uploaded_file)
        
        # DEBUG: Show what the file looks like immediately after upload
        st.subheader("Step 1: Raw Data Check")
        st.write("This is what I see in your Excel file:")
        st.dataframe(raw_df.head(), use_container_width=True)

        # Standardize column names
        raw_df.columns = [str(c).strip().title() for c in raw_df.columns]
        
        if 'Day' in raw_df.columns and 'Closing Balance' in raw_df.columns:
            
            # CRITICAL FIX: Convert 'Day' to datetime and drop rows where Date or Balance is missing
            raw_df['Day'] = pd.to_datetime(raw_df['Day'], errors='coerce')
            raw_df = raw_df.dropna(subset=['Day', 'Closing Balance'])
            
            # Sort and set index
            raw_df = raw_df.sort_values('Day').set_index('Day')
            
            # Reindex for missing days
            all_days = pd.date_range(start=raw_df.index.min(), end=raw_df.index.max(), freq='D')
            df = raw_df.reindex(all_days)
            
            # Interpolate
            df['Closing Balance'] = df['Closing Balance'].interpolate(method='linear')
            df = df.reset_index().rename(columns={'index': 'Day'})

            # DEBUG: Show processed data
            st.subheader("Step 2: Processed Data (Interpolated)")
            st.write("This is the data being sent to the graph:")
            st.dataframe(df, use_container_width=True)

            # --- 3. Plotting ---
            if not df.empty:
                st.subheader("Step 3: Inventory Trend")
                fig = px.area(df, x='Day', y='Closing Balance', 
                              title="Daily Inventory Balance",
                              labels={'Closing Balance': 'Units', 'Day': 'Date'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculations
                min_inv = df['Closing Balance'].min()
                avg_inv = df['Closing Balance'].mean()
                
                st.divider()
                st.subheader("💰 Impact Analysis")
                total_red = reduction_qty + (min_inv * reduction_pct)
                cash_released = total_red * unit_cost
                
                c1, c2 = st.columns(2)
                c1.metric("Min Inventory", f"{min_inv:,.0f}")
                c2.metric("Cash Released", f"${cash_released:,.2f}")
            else:
                st.warning("The processed dataframe is empty. Check your date formats.")

        else:
            st.error(f"Column mismatch! Found: {list(raw_df.columns)}. Need: 'Day' and 'Closing Balance'")
            
    except Exception as e:
        st.error(f"Critical Error: {e}")
