import sqlite3
import os
import shutil

def get_db_path():
    app_dir = os.path.dirname(__file__) or '.'
    is_read_only = not os.access(app_dir, os.W_OK)
    is_cloud = any(k in os.environ for k in ('VERCEL', 'VERCEL_ENV', 'AWS_LAMBDA_FUNCTION_NAME', 'LAMBDA_TASK_ROOT'))
    
    if is_cloud or is_read_only:
        tmp_db = '/tmp/somaiyasat.db'
        bundled_db = os.path.join(app_dir, 'somaiyasat.db')
        if not os.path.exists(tmp_db):
            if os.path.exists(bundled_db):
                try:
                    shutil.copyfile(bundled_db, tmp_db)
                except Exception:
                    pass
        if os.path.exists(tmp_db):
            try:
                os.chmod(tmp_db, 0o666)
            except Exception:
                pass
        return tmp_db
    return os.path.join(app_dir, 'somaiyasat.db')


def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Enable Foreign Key Support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Deployer Table (SomaiyaPod)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deployer (
        deployer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pod_name TEXT NOT NULL,
        ejection_status TEXT CHECK(ejection_status IN ('Locked', 'Armed', 'Ejected')) DEFAULT 'Locked',
        ejection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Satellite Table (SomaiyaSat) - Demonstrating Foreign Key (Referential Integrity)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS satellite (
        sat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        deployer_id INTEGER NOT NULL,
        callsign TEXT NOT NULL UNIQUE,
        operational_status TEXT CHECK(operational_status IN ('Dormant', 'Detumbling', 'Active', 'SafeMode')) DEFAULT 'Dormant',
        FOREIGN KEY (deployer_id) REFERENCES deployer(deployer_id) ON DELETE CASCADE
    );
    """)

    # 3. Telemetry Table (TT&C Data) - Relational Logging with Constraints
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sat_id INTEGER NOT NULL,
        battery_pct REAL CHECK(battery_pct >= 0 AND battery_pct <= 100),
        solar_voltage REAL CHECK(solar_voltage >= 0),
        temperature REAL,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sat_id) REFERENCES satellite(sat_id) ON DELETE CASCADE
    );
    """)

    # 4. Transmission Queue Table - Handling Multi-Mode Comms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transmission_queue (
        packet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sat_id INTEGER NOT NULL,
        mode TEXT CHECK(mode IN ('M17 Voice', 'Codec2 Voice', 'SSTV Image', 'TT&C Beacon')) NOT NULL,
        payload_data TEXT NOT NULL,
        priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')) DEFAULT 'Medium',
        status TEXT CHECK(status IN ('Pending', 'Transmitted', 'Failed')) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sat_id) REFERENCES satellite(sat_id) ON DELETE CASCADE
    );
    """)

    # 5. Database Indexes (Unit 4: Indexing for fast search)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(recorded_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON transmission_queue(status, priority);")

    # 6. Database Trigger (Unit 2.5: Triggers)
    # When Deployer status updates to 'Ejected', automatically update Satellite to 'Active'
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_deploy_satellite
    AFTER UPDATE OF ejection_status ON deployer
    WHEN NEW.ejection_status = 'Ejected'
    BEGIN
        UPDATE satellite SET operational_status = 'Active' WHERE deployer_id = NEW.deployer_id;
    END;
    """)

    # 7. Database View (Unit 2.3: Views & Joins)
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_mission_overview AS
    SELECT 
        s.sat_id,
        s.callsign,
        s.operational_status,
        d.pod_name,
        d.ejection_status,
        COUNT(t.telemetry_id) AS total_telemetry_reports,
        ROUND(AVG(t.battery_pct), 2) AS avg_battery_pct
    FROM satellite s
    JOIN deployer d ON s.deployer_id = d.deployer_id
    LEFT JOIN telemetry t ON s.sat_id = t.sat_id
    GROUP BY s.sat_id;
    """)

    # Seed default sample record if empty
    cursor.execute("SELECT COUNT(*) FROM deployer;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO deployer (pod_name, ejection_status) VALUES ('SomaiyaPod-1', 'Ejected');")
        deployer_id = cursor.lastrowid
        cursor.execute("INSERT INTO satellite (deployer_id, callsign, operational_status) VALUES (?, 'VU2SOM-SAT', 'Active');", (deployer_id,))
        sat_id = cursor.lastrowid

        # Sample telemetry
        cursor.execute("INSERT INTO telemetry (sat_id, battery_pct, solar_voltage, temperature) VALUES (?, 94.5, 4.2, 18.2);", (sat_id,))
        cursor.execute("INSERT INTO telemetry (sat_id, battery_pct, solar_voltage, temperature) VALUES (?, 91.0, 3.9, 19.5);", (sat_id,))

        # Sample transmissions
        cursor.execute("INSERT INTO transmission_queue (sat_id, mode, payload_data, priority, status) VALUES (?, 'M17 Voice', 'CQ CQ SomaiyaSat test broadcast', 'High', 'Pending');", (sat_id,))
        cursor.execute("INSERT INTO transmission_queue (sat_id, mode, payload_data, priority, status) VALUES (?, 'SSTV Image', 'earth_low_orbit_cam01.jpg', 'Medium', 'Pending');", (sat_id,))
        cursor.execute("INSERT INTO transmission_queue (sat_id, mode, payload_data, priority, status) VALUES (?, 'TT&C Beacon', 'HEALTH_OK;BAT=94.5', 'Critical', 'Transmitted');", (sat_id,))

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with Tables, Constraints, Triggers, Views, and Indexes.")
