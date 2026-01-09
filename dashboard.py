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
        st.subheader("🚨 Recent Security Alerts")
        df_suspicious = pd.read_sql("SELECT rejection_reason, timestamp, raw_record FROM suspicious_events ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(df_suspicious, use_container_width=True)
        
    st.divider()

    # --- RNG Analysis (The Fixed Section) ---
    st.subheader("🎲 RNG Analysis: Value Spread")
    st.markdown("*Visualizing the Min/Max roll range for each item.*")

    df_spread = pd.read_sql("SELECT id, item_name, item_value FROM valid_loot", conn)

    if not df_spread.empty:
        # 1. Filter
        all_items = df_spread['item_name'].unique()
        selected_items = st.multiselect("Select Loot Tables:", all_items, default=all_items)
        filtered_spread = df_spread[df_spread['item_name'].isin(selected_items)]
        
        if not filtered_spread.empty:
            # 1. UI Control
            chart_style = st.radio(
                "Select Visualization Style:", 
                ["📦 Box Plot (Summary)", "🔵 Frequency Bubbles (Volume)"],
                horizontal=True
            )

            # 2. Define the Base (Shared Data)
            # note: 'item_name:N' tells Altair this is a Category (Nominal)
            base = alt.Chart(filtered_spread).encode(
                x=alt.X('item_name:N', title=None, axis=alt.Axis(grid=False, labelAngle=0)),
                y=alt.Y('item_value:Q', title='Gold Value'),
                color='item_name:N'
            )

            if chart_style == "📦 Box Plot (Summary)":
                # A. The Visual Layer (The Box Plot)
                visual_box = base.mark_boxplot(
                    extent='min-max', 
                    size=50,
                    rule={'strokeWidth': 4},
                    median={'strokeWidth': 4, 'color': 'black'},
                    box={'strokeWidth': 2}
                )
                
                # B. The Interaction Layer (The "Ghost")
                # We plot invisible points (opacity=0) just to catch the mouse scroll
                ghost_layer = base.mark_circle(opacity=0).encode(
                    tooltip=[alt.Tooltip('item_name', title='Item')]
                ).interactive() # <--- This handles the zoom!
                
                # Combine them: The Ghost controls the scale for the Box
                final_chart = visual_box + ghost_layer
            
            else:
                # View B: The Frequency Bubbles
                # These are simple shapes, so they support native interactive()
                final_chart = base.mark_circle().encode(
                    size=alt.Size('count()', title='Count', scale=alt.Scale(range=[50, 500])),
                    tooltip=['item_name', 'item_value', alt.Tooltip('count()', title='Count')]
                ).interactive()

            # 3. Render
            st.altair_chart(
                final_chart, 
                use_container_width=True,
                theme="streamlit",
                key="rng_chart_v4" # Bump key to force refresh
            )
            
            # 5. Stats Table
            st.caption("Detailed Statistics")
            stats = filtered_spread.groupby("item_name")['item_value'].describe()
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