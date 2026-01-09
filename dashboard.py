import streamlit as st
import mysql.connector
import pandas as pd
import os

# Page Config
st.set_page_config(
    page_title="Game Economy Monitor",
    page_icon="⚔️",
    layout="wide"
)

# DB Connection
def get_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Sidebar Controls
st.sidebar.title("Controls")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()
    
st.title("⚔️ Game Economy Real-Time Monitor")

try:
    conn = get_connection()
    
    # KPI Metrics
    # Use SQL to count rows quickly
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM valid_loot")
    valid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM suspicious_events")
    suspicious_count = cursor.fetchone()[0]
    
    # Display Metrics in 3 columns
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Valid Loot Drops", valid_count)
    col2.metric("🚫 Suspicious Events", suspicious_count, delta_color="inverse")
    
    st.divider()
    
    # Chart and Analysis
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Loot Distribution")
        df_loot = pd.read_sql("""
            SELECT item_name, COUNT(*) as drop_count
            FROM valid_loot
            GROUP BY item_name
        """, conn)
        
        if not df_loot.empty:
            st.bar_chart(df_loot.set_index('item_name'))
        else:
            st.info("No valid loot data yet.")
    
    with col_right:
        st.subheader("🚨 Recent Security Alerts")
        df_suspicious = pd.read_sql("SELECT rejection_reason, timestamp, raw_record FROM suspicious_events ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(df_suspicious, use_container_width=True)
        
    st.divider()
    st.subheader("🎲 RNG Analysis: Value Spread")
    
    st.markdown("""
    *Visualizing the Min/Max roll range for each item. 
    A taller vertical spread means higher variance in item quality.*
    """)

    # 1. Get the data
    df_spread = pd.read_sql("SELECT id, item_name, item_value FROM valid_loot", conn)

    if not df_spread.empty:
        # Interactive Filter
        all_items = df_spread['item_name'].unique()
        selected_items = st.multiselect("Select Loot Tables to Inspect:", all_items, default=all_items)
        
        # Filter Logic
        filtered_spread = df_spread[df_spread['item_name'].isin(selected_items)]

        # 2. The Chart
        # X-Axis = The specific drop event (ID)
        # Y-Axis = The Gold Value rolled
        # Color  = The Item Name
        st.scatter_chart(
            filtered_spread,
            x='id',
            y='item_value',
            color='item_name',
            size=50  # Dot size
        )
        
        # 3. Statistics Table (Bonus!)
        # Show exact Min/Max/Average for the selected items
        if not filtered_spread.empty:
            st.caption("Detailed Statistics")
            stats = filtered_spread.groupby("item_name")['item_value'].agg(['min', 'max', 'mean', 'count'])
            st.dataframe(stats)
            
    else:
        st.info("No loot data recorded yet.")
        
    conn.close()

except Exception as e:
    st.error(f"Database Error: {e}")