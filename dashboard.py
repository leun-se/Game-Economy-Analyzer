import streamlit as st
import mysql.connector
import pandas as pd
import os
import subprocess
import pipeline
import altair as alt

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
st.sidebar.title("⚙️ Control Plane")

# 1. The Input Field
amount = st.sidebar.number_input("Loot to Generate", min_value=10, max_value=10000, value=100, step=10)

# 2. The Magic Button
if st.sidebar.button(f"🚀 Generate {amount} Drops"):
    status_text = st.sidebar.empty()
    
    try:
        # Step A: Run Java
        status_text.info("🔨 Running Java Generator...")
        
        # We force a re-compile inside the container so the versions match
        compile_result = subprocess.run(["javac", "LootGenerator.java"], capture_output=True, text=True)
        if compile_result.returncode != 0:
            st.error(f"Compilation Failed: {compile_result.stderr}")
            st.stop() # Stop execution here
            
        # We call the java command just like in a terminal
        result = subprocess.run(
            ["java", "LootGenerator", str(amount)], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            st.error(f"Java Error: {result.stderr}")
        else:
            # Step B: Run Python Pipeline
            status_text.info("📥 Ingesting to MySQL...")
            pipeline.run_pipeline() # We call the function from your other script!
            
            status_text.success("✅ Job Complete!")
            st.rerun() # Refresh the dashboard to see new data
            
    except Exception as e:
        st.error(f"Pipeline Failed: {e}")

if st.sidebar.button("🔄 Refresh View Only"):
    st.rerun()

if st.sidebar.button("🗑️ Reset Database"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE valid_loot")
    cursor.execute("TRUNCATE TABLE suspicious_events")
    conn.close()
    st.sidebar.success("Database wiped clean!")
    st.rerun()
    
st.title("⚔️ Game Economy Real-Time Monitor")

try:
    conn = get_connection()
    
    # --- KPI Metrics ---
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM valid_loot")
    valid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM suspicious_events")
    suspicious_count = cursor.fetchone()[0]
    cursor.close() # Good practice to close the cursor
    
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Valid Loot Drops", valid_count)
    col2.metric("🚫 Suspicious Events", suspicious_count, delta_color="inverse")
    
    st.divider()
    
    # --- Top Charts ---
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
        st.subheader("🚨 Security Alerts")
        
        # 1. Fetch the data
        df_security = pd.read_sql("""
            SELECT rejection_reason, timestamp, raw_record 
            FROM suspicious_events 
            ORDER BY id DESC LIMIT 1000
        """, conn)

        if not df_security.empty:
            # 2. THE CLEAN FEED
            st.dataframe(
                df_security, 
                use_container_width=True, 
                hide_index=True,
                height=400  # Keeps the dashboard aligned
            )
        else:
            st.success("No security alerts found.")
        
    st.divider()

    # --- RNG Analysis (The Fixed Section) ---
    st.subheader("🎲 RNG Analysis: Value Spread")
    st.markdown("*Visualizing the Min/Max roll range for each item.*")

    df_spread = pd.read_sql("SELECT id, item_name, item_value FROM valid_loot", conn)

    if not df_spread.empty:
        # 1. OPTIMIZATION: Pre-calculate Statistics in Python
        # This prevents sending thousands of raw rows to the browser
        
        # A. For Sorting & Filtering (Median)
        item_stats = df_spread.groupby('item_name')['item_value'].median().sort_values()
        sorted_items = item_stats.index.tolist()

        # B. For the "Ghost Layer" (Only need Min and Max to define zoom boundaries)
        # Instead of plotting 10,000 points, we plot 2 points per item.
        # This is the secret to 60fps zooming.
        bounds_df = df_spread.groupby('item_name')['item_value'].agg(['min', 'max']).reset_index()
        bounds_df = bounds_df.melt(id_vars='item_name', value_name='item_value')

        # C. For the Bubbles (Pre-count frequencies)
        bubble_df = df_spread.groupby(['item_name', 'item_value']).size().reset_index(name='count')

        # 2. FILTER CONTROLS
        selected_items = st.multiselect(
            "Select Loot Tables to Inspect:", 
            sorted_items, 
            default=sorted_items[:5] 
        )
        
        # Filter our optimized datasets
        # Note: We filter the summary tables, not the raw massive table!
        filtered_bounds = bounds_df[bounds_df['item_name'].isin(selected_items)]
        filtered_bubbles = bubble_df[bubble_df['item_name'].isin(selected_items)]
        
        # We still need the raw data for the Box Plot stats calculation, but NOT for plotting
        filtered_raw = df_spread[df_spread['item_name'].isin(selected_items)]

        if not filtered_bounds.empty:
            # 3. UI CONTROLS
            col_controls1, col_controls2 = st.columns([2, 1])
            with col_controls1:
                chart_style = st.radio(
                    "Select Visualization Style:", 
                    ["📦 Box Plot (Summary)", "🔵 Frequency Bubbles (Volume)"],
                    horizontal=True
                )
            with col_controls2:
                use_log_scale = st.checkbox("Use Log Scale", value=False)

            y_scale = alt.Scale(type='symlog') if use_log_scale else alt.Scale(type='linear')

            # 4. CHART CONSTRUCTION
            
            if chart_style == "📦 Box Plot (Summary)":
                # Base for Box Plot uses the RAW data (Altair handles box stats efficiently)
                base = alt.Chart(filtered_raw).properties(height=600).encode(
                    x=alt.X('item_name:N', title=None, axis=alt.Axis(grid=False, labelAngle=0)),
                    y=alt.Y('item_value:Q', title='Gold Value', scale=y_scale),
                    color=alt.Color('item_name:N', legend=None)
                )

                visual_box = base.mark_boxplot(
                    extent='min-max', 
                    size=80,
                    opacity=0.7,
                    rule={'strokeWidth': 3, 'color': 'white'},
                    ticks={'strokeWidth': 3, 'color': 'white', 'size': 20},
                    median={'strokeWidth': 4, 'color': 'white'},
                    box={'strokeWidth': 2}
                )
                
                # --- OPTIMIZED GHOST LAYER ---
                # We use 'filtered_bounds' (tiny) instead of 'filtered_raw' (huge)
                # The Zoom Engine thinks it's looking at the whole dataset, but it's just the edges.
                ghost_layer = alt.Chart(filtered_bounds).mark_circle(opacity=0).encode(
                    x='item_name:N',
                    y='item_value:Q',
                    tooltip=[alt.Tooltip('item_name', title='Item')]
                ).interactive()
                
                final_chart = visual_box + ghost_layer
            
            else:
                # OPTIMIZED BUBBLES
                # We use 'filtered_bubbles' where counts are already calculated
                base = alt.Chart(filtered_bubbles).properties(height=600).encode(
                    x=alt.X('item_name:N', title=None, axis=alt.Axis(grid=False, labelAngle=0)),
                    y=alt.Y('item_value:Q', title='Gold Value', scale=y_scale),
                    color=alt.Color('item_name:N', legend=None)
                )
                
                final_chart = base.mark_circle().encode(
                    # We use the pre-calculated 'count' column
                    size=alt.Size('count', title='Count', scale=alt.Scale(range=[50, 1000])),
                    tooltip=['item_name', 'item_value', alt.Tooltip('count', title='Count')]
                ).interactive()

            # 5. RENDER
            st.altair_chart(
                final_chart, 
                use_container_width=True, 
                theme="streamlit", 
                key=f"rng_chart_opt_{use_log_scale}"
            )
            
            # 6. STATISTICS
            st.caption("Detailed Statistics")
            stats = filtered_raw.groupby("item_name")['item_value'].describe()
            stats = stats[['count', 'mean', 'min', '25%', '50%', '75%', 'max']]
            stats.columns = ['Count', 'Avg', 'Min', 'Q1', 'Median', 'Q3', 'Max']
            st.dataframe(stats.style.format("{:.2f}"))
            
        else:
            st.info("No items selected.")
    else:
        st.info("No loot data recorded yet.")
        
    conn.close()

except Exception as e:
    st.error(f"Database Error: {e}")