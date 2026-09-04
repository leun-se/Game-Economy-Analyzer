# Game Economy Simulation & Analytics Pipeline

A full-stack data engineering project that simulates a live MMO game economy, processes transaction streams in real-time, and visualizes economic health using a custom-built dashboard.

The goal of this project was to build a resilient pipeline capable of distinguishing between legitimate "high-roller" transactions (rare drops) and actual game-breaking exploits (duped items/integer overflows), while optimizing frontend performance for large datasets.

### 🏗 Architecture

The system runs entirely in a containerized **Docker** environment with three distinct services:

* **Generator (Java):** Simulates loot drops using Gaussian distributions and relative volatility logic.
* **Pipeline (Python):** An ETL process that validates raw JSON logs, filters corrupt data, and loads clean records into MySQL.
* **Dashboard (Streamlit):** An interactive analytics tool with custom Altair visualizations and 60fps zooming optimizations.

**Tech Stack:** `Java` `Python` `MySQL` `Docker` `Streamlit` `Pandas` `Altair`

---

### 🚀 Key Features

#### 1. Realistic Economy Simulation (Java)
Instead of simple random numbers, the loot generator uses **Gaussian Math (Normal Distribution)** to simulate realistic market fluctuations.
* **Proportional Volatility:** Item prices fluctuate by a percentage (e.g., ±20%) rather than a fixed flat amount.
* **Rarity Tiers:** Handles everything from "Common Trash" to "Legendary Artifacts."
* **Chaos Engineering:** Randomly injects "bad data" (negative values, missing fields) and "exploits" (values > server cap) to test pipeline resilience.

#### 2. Security & Validation (Python ETL)
The pipeline acts as a firewall between the raw logs and the analytics database.
* **Exploit Detection:** Automatically flags items exceeding the global gold cap (e.g., > 2,000g) as "Duped Items" and routes them to a separate Security Table.
* **Data Cleaning:** Catches integer overflows and malformed JSON before they hit the database.
* **Valid Outliers:** Smart filtering allows legitimate rare drops (e.g., a 1,500g Dragon Egg) to pass through while blocking illegal 10,000g hacks.

#### 3. Optimized Analytics Dashboard
A custom frontend built to handle high-density data without browser lag.
* **"Ghost Layer" Rendering:** Solved a rendering bottleneck by pre-calculating outliers in Python. The chart draws a summary Box Plot and only renders interactive tooltips for specific outliers, reducing DOM elements by 99%.
* **Dynamic Log Scaling:** Includes a toggleable Logarithmic Scale to visualize massive gaps between common items (10g) and rare artifacts (1,500g).
* **Live Security Feed:** A dedicated scrollable widget for monitoring rejected transactions in real-time.

---

### 🛠️ How to Run

**Prerequisites:** Docker Desktop installed and running.

1.  **Clone the repository:**
    ```bash
    git clone <https://github.com/leun-se/Game-Economy-Analyzer.git>
    cd Game-Economy-Analyzer
    ```

2.  **Start the services:**
    ```bash
    docker-compose up --build
    ```

3.  **Access the Dashboard:**
    Open your browser to `http://localhost:8501`.

4.  **Simulate Data:**
    * Use the sidebar to **"Generate 1000 Drops"**.
    * Watch the pipeline compile the Java code, generate logs, and ingest them instantly.
    * Toggle **"Frequency Bubbles"** to see the Gaussian distribution in action.

---

### 🧪 Engineering Trade-offs

* **Handling Outliers:** I initially tried to plot every single data point, but this caused significant browser lag when zooming. I switched to a hybrid approach: using Altair to render the statistical box plot and a separate "Ghost Layer" specifically for outlier interaction. This maintained statistical accuracy while keeping the UI responsive.
* **Visualizing Scale:** A linear scale made common items look like a flat line when high-value items were present. Implementing a dynamic **Symlog (Symmetric Log)** scale allows analysts to compare the "Rusty Dagger" and "Dragon Egg" side-by-side without losing detail.
