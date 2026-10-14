from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import init_db, get_db

app = Flask(__name__)

# Ensure DB initialized
init_db()

@app.route('/')
def index():
    db = get_db()
    overview = db.execute("SELECT * FROM v_mission_overview").fetchall()
    deployers = db.execute("SELECT * FROM deployer").fetchall()
    satellites = db.execute("SELECT s.*, d.pod_name FROM satellite s JOIN deployer d ON s.deployer_id = d.deployer_id").fetchall()
    telemetry = db.execute("SELECT t.*, s.callsign FROM telemetry t JOIN satellite s ON t.sat_id = s.sat_id ORDER BY t.recorded_at DESC LIMIT 15").fetchall()
    transmissions = db.execute("SELECT q.*, s.callsign FROM transmission_queue q JOIN satellite s ON q.sat_id = s.sat_id ORDER BY q.created_at DESC").fetchall()
    db.close()
    return render_template('index.html', overview=overview, deployers=deployers, satellites=satellites, telemetry=telemetry, transmissions=transmissions)

@app.route('/database-view')
def database_view():
    db = get_db()
    deployers = db.execute("SELECT * FROM deployer").fetchall()
    satellites = db.execute("SELECT * FROM satellite").fetchall()
    telemetry = db.execute("SELECT * FROM telemetry ORDER BY recorded_at DESC").fetchall()
    transmissions = db.execute("SELECT * FROM transmission_queue ORDER BY created_at DESC").fetchall()
    
    # Table metadata for schema visualization
    schema_info = {
        'deployer': db.execute("PRAGMA table_info(deployer)").fetchall(),
        'satellite': db.execute("PRAGMA table_info(satellite)").fetchall(),
        'telemetry': db.execute("PRAGMA table_info(telemetry)").fetchall(),
        'transmission_queue': db.execute("PRAGMA table_info(transmission_queue)").fetchall(),
    }
    
    # Triggers and Views
    triggers = db.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
    views = db.execute("SELECT name, sql FROM sqlite_master WHERE type='view'").fetchall()
    indexes = db.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()
    
    db.close()
    return render_template('database_view.html', 
                           deployers=deployers, 
                           satellites=satellites, 
                           telemetry=telemetry, 
                           transmissions=transmissions,
                           schema_info=schema_info,
                           triggers=triggers,
                           views=views,
                           indexes=indexes)

# ----------------- CRUD: TELEMETRY -----------------
@app.route('/telemetry/create', methods=['POST'])
def create_telemetry():
    sat_id = request.form.get('sat_id')
    battery_pct = float(request.form.get('battery_pct'))
    solar_voltage = float(request.form.get('solar_voltage'))
    temperature = float(request.form.get('temperature'))
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO telemetry (sat_id, battery_pct, solar_voltage, temperature) VALUES (?, ?, ?, ?)",
            (sat_id, battery_pct, solar_voltage, temperature)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Database Error: {e}", 400
    finally:
        db.close()
    return redirect(url_for('index'))

@app.route('/telemetry/delete/<int:id>', methods=['POST'])
def delete_telemetry(id):
    db = get_db()
    db.execute("DELETE FROM telemetry WHERE telemetry_id = ?", (id,))
    db.commit()
    db.close()
    return redirect(url_for('index'))

# ----------------- CRUD: TRANSMISSION QUEUE -----------------
@app.route('/transmission/create', methods=['POST'])
def create_transmission():
    sat_id = request.form.get('sat_id')
    mode = request.form.get('mode')
    payload = request.form.get('payload_data')
    priority = request.form.get('priority')
    
    db = get_db()
    try:
        db.execute(
            "INSERT INTO transmission_queue (sat_id, mode, payload_data, priority, status) VALUES (?, ?, ?, ?, 'Pending')",
            (sat_id, mode, payload, priority)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Database Error: {e}", 400
    finally:
        db.close()
    return redirect(url_for('index'))

@app.route('/transmission/update_status/<int:id>', methods=['POST'])
def update_transmission_status(id):
    new_status = request.form.get('status')
    db = get_db()
    db.execute("UPDATE transmission_queue SET status = ? WHERE packet_id = ?", (new_status, id))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/transmission/delete/<int:id>', methods=['POST'])
def delete_transmission(id):
    db = get_db()
    db.execute("DELETE FROM transmission_queue WHERE packet_id = ?", (id,))
    db.commit()
    db.close()
    return redirect(url_for('index'))

# ----------------- TRIGGER DEMONSTRATION -----------------
@app.route('/deployer/update_status/<int:id>', methods=['POST'])
def update_deployer(id):
    status = request.form.get('ejection_status')
    db = get_db()
    db.execute("UPDATE deployer SET ejection_status = ? WHERE deployer_id = ?", (status, id))
    db.commit()
    db.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
