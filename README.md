# SomaiyaSat Mission Control System

A full-stack DBMS CRUD web application for managing satellite deployment, telemetry logging (TT&C), and multi-mode amateur radio transmission queues for SomaiyaSat & SomaiyaPod.

## Features
- **Mission Dashboard:** Live monitoring of PocketQube operational status and deployer states.
- **Relational DBMS (3NF / BCNF):** SQLite database modeling Deployer, Satellite, Telemetry, and Transmission Queue.
- **Advanced SQL Concepts:**
  - **Foreign Keys & Constraints:** Domain constraints (`CHECK`) and referential integrity (`ON DELETE CASCADE`).
  - **Triggers:** Auto-transition satellite state to `Active` on deployer ejection.
  - **Views & Aggregation:** `v_mission_overview` combining multi-table joins with `AVG()` and `COUNT()`.
  - **B-Tree Indexing:** Accelerated time-series and priority queries.
  - **ACID Transactions:** Insert/update operations with commit and rollback handling.
- **Schema Explorer:** Interactive E-R diagram (Mermaid.js) and database structure visualization (`/database-view`).

## Tech Stack
- **Backend:** Python / Flask
- **Database:** SQLite3
- **Frontend:** HTML5, Tailwind CSS, Mermaid.js

## Running Locally
1. Install Flask:
   ```bash
   pip install flask
   ```
2. Start the application:
   ```bash
   python app.py
   ```
3. Open your browser at:
   - Dashboard: `http://127.0.0.1:5000/`
   - Schema Explorer: `http://127.0.0.1:5000/database-view`
