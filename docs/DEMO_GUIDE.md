# Laboratory Examination Demonstration Guide
## Smart Agriculture Monitoring System

This document provides examiners and students with exact, reproducible steps to demonstrate every functional and security feature required during the Secure Software Engineering laboratory examination.

---

### PRE-REQUISITES & STARTING THE APPLICATION

#### Option A: Running with Docker Compose (Recommended)
```bash
docker compose build
docker compose up -d
docker compose ps
```
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`

#### Option B: Running Locally (Fast Native Mode)
1. **Start Backend**:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Start IoT Simulator**:
   ```bash
   python iot-simulator/simulator.py --loop --interval 5
   ```

---

### DEMONSTRATION SCENARIOS

#### DEMO 1: Normal Environmental Monitoring
1. Open the web browser to `http://localhost:3000`.
2. Click **Login as Admin** (or enter `admin` / `Admin@Secure2026!`).
3. View the **Dashboard**:
   - Soil Moisture, Greenhouse Temperature, Relative Humidity, and Water Reservoir Level cards are live.
   - All badges display green **NORMAL** status.
   - Weather widget displays diurnal temperature curves and solar radiation flux.

#### DEMO 2: Low Soil Moisture & Automatic Irrigation Activation
1. Run the simulator scenario:
   ```bash
   python iot-simulator/simulator.py --scenario dry_soil
   ```
2. **Observed System Behavior**:
   - Soil moisture drops to 18% (< configured min of 30%).
   - The automation engine evaluates the condition and verifies water level > 15%.
   - Irrigation Pump (`ACT_PUMP_01`) turns **ON** automatically.
   - Equipment Alert is generated: *"Automatic Irrigation Activated"*.
   - Audit log records `ACTUATOR_STATE_CHANGE` event.

#### DEMO 3: Safe Irrigation Stop upon Target Recovery
1. Run the simulator scenario:
   ```bash
   python iot-simulator/simulator.py --scenario safe_stop
   ```
2. **Observed System Behavior**:
   - Soil moisture reaches 65% (>= configured target of 60%).
   - Irrigation Pump automatically switches to **OFF**.
   - System alert logged: *"Automatic Irrigation Stopped: Safe Target Reached"*.

#### DEMO 4: Low Water Level Safety Interlock (Dry-Run Prevention)
1. Run the simulator scenario:
   ```bash
   python iot-simulator/simulator.py --scenario low_water
   ```
2. **Observed System Behavior**:
   - Water reservoir level drops to 8% (< safety cutoff of 15%).
   - If the pump is running, an immediate emergency cutoff is executed.
   - If soil moisture is dry, pump startup is **hard-locked**.
   - A **CRITICAL** alarm is raised: *"Critical Water Reservoir Depletion - Pump Inhibited"*.
   - Audit event `SAFETY_INTERLOCK_TRIGGERED` is stored in the database.

#### DEMO 5: Sensor Spoofing Protection
1. Execute the rogue sensor attack script:
   ```bash
   python iot-simulator/simulator.py --scenario spoofing
   ```
   *Or via curl:*
   ```bash
   curl -X POST http://localhost:8000/api/sensors/reading \
     -H "Content-Type: application/json" \
     -d '{"device_id":"DEV_ROGUE_99","farm_id":"farm_1","sensor_type":"soil_moisture","value":25.0,"unit":"%"}'
   ```
2. **Observed Security Behavior**:
   - The backend rejects the request with **HTTP 400 Bad Request** (`SENSOR_SPOOF_DETECTED`).
   - A **CRITICAL** Security Alert is generated and appears in the UI.
   - Navigate to the **Audit Logs** tab in the dashboard to inspect the recorded `SENSOR_SPOOF_ATTEMPT` event.

#### DEMO 6: False Environmental Data Protection
1. Run the impossible value attack:
   ```bash
   python iot-simulator/simulator.py --scenario false_data
   ```
   *Or via curl:*
   ```bash
   curl -X POST http://localhost:8000/api/sensors/reading \
     -H "Content-Type: application/json" \
     -d '{"device_id":"DEV_ENV_01","farm_id":"farm_1","sensor_type":"temperature","value":999.0,"unit":"°C","auth_token":"env_secret_key_01"}'
   ```
2. **Observed Security Behavior**:
   - Value 999.0°C violates physical bounds `[-10.0, 60.0]`.
   - Backend rejects with **HTTP 400 Bad Request** (`FALSE_ENVIRONMENTAL_DATA`).
   - Audit event `FALSE_DATA_DETECTED` is recorded.

#### DEMO 7: Protection Against Unauthorized Actuator Control
1. Logout of the application, then click **Login as Viewer** (`viewer` / `Viewer@Secure2026!`).
2. Navigate to the **Actuator Control** tab.
3. Click **Start** on the Irrigation Pump.
4. **Observed Security Behavior**:
   - The backend rejects the request with **HTTP 403 Forbidden** (*"Forbidden: Insufficient privileges"*).
   - An audit event `UNAUTHORIZED_ACCESS` is recorded with the viewer's username and IP address.

#### DEMO 8: Authorized Administrator Actuator Control
1. Logout and click **Login as Admin** (`admin` / `Admin@Secure2026!`).
2. Navigate to **Actuator Control** and click **Start** on the Greenhouse Fan.
3. **Observed Security Behavior**:
   - Command succeeds with **HTTP 200 OK**.
   - Actuator status changes to **ON**.
   - Audit log records `ACTUATOR_COMMAND` with result `SUCCESS`.

#### DEMO 9: Availability Protection & Rate Limiting
1. Attempt repeated unauthorized logins (>10 per minute):
   ```bash
   for i in {1..15}; do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"bad","password":"bad"}'; done
   ```
2. **Observed Security Behavior**:
   - After the 10th request, the SlowAPI limiter returns **HTTP 429 Too Many Requests**, protecting against credential stuffing and DoS attacks.

#### DEMO 10: Device Suspension & Privilege Revocation
1. Log in as **Admin** and navigate to the **Device Management** tab.
2. Click **Suspend Node** on `DEV_SOIL_01`.
3. The device status transitions to `suspended`.
4. Run:
   ```bash
   curl -X POST http://localhost:8000/api/sensors/reading \
     -H "Content-Type: application/json" \
     -d '{"device_id":"DEV_SOIL_01","farm_id":"farm_1","sensor_type":"soil_moisture","value":45.0,"unit":"%","auth_token":"soil_secret_key_01"}'
   ```
5. **Observed Security Behavior**:
   - Ingestion is rejected with **HTTP 400 Bad Request** (`DEVICE_SUSPENDED`).
   - Security alert: *"Suspended Device Telemetry Blocked"*.
   - Click **Reactivate** to restore normal operation.
