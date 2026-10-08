# Security Architecture & Threat Model
## Smart Agriculture Monitoring System

### 1. Security Principles Implemented

| Security Principle | Implementation in System |
|--------------------|--------------------------|
| **Least Privilege** | Role-Based Access Control (ADMIN, OPERATOR, VIEWER). Mosquitto Topic ACLs isolate device read/write privileges. |
| **Defense in Depth** | Multi-tier validation: Frontend checks -> Network rate limiter -> JWT authorization -> Pydantic structure check -> Physical boundary rules -> Statistical anomaly jump detector -> Watchdog timeouts. |
| **Fail-Safe Defaults** | If a sensor loses signal or sends invalid/spoofed data, actuators fail safe to OFF. If the water reservoir is depleted, pumps are hard locked. |
| **Non-Repudiation** | Immutable Audit Log table records all administrative, operational, and security-critical actions with timestamp, user/node ID, and IP address. |
| **Anti-Spoofing** | Device pre-shared authentication tokens verified via constant-time HMAC comparison. Topic-to-payload identity matching. |
| **Anti-Tampering** | Timestamps validated against server clock (rejects readings >300s in past or >60s in future to prevent replay attacks). |

### 2. Explicit Threats Addressed & Countermeasures

#### Threat 1: Sensor Spoofing
- **Threat Vector**: An attacker attempts to inject false soil moisture or temperature readings using an unauthorized client or rogue device ID.
- **Countermeasure**:
  1. The backend verifies that the device ID exists in the registered `devices` inventory.
  2. If the device is not registered, the reading is immediately rejected with HTTP 400 / MQTT drop.
  3. A `CRITICAL` severity security alert is generated.
  4. An immutable audit log entry (`SENSOR_SPOOF_ATTEMPT`) is recorded.
  5. Cryptographic pre-shared secret verification ensures only genuine hardware can publish telemetry.

#### Threat 2: Unauthorized Actuator Control
- **Threat Vector**: A malicious user or compromised low-privilege account attempts to activate water pumps or greenhouse equipment to flood fields or overheat crops.
- **Countermeasure**:
  1. Actuator control endpoints enforce backend RBAC (`require_role(["ADMIN", "OPERATOR"])`).
  2. Frontend button restrictions are purely ergonomic; calling `POST /api/actuators/{id}/command` directly as a `VIEWER` is intercepted at the controller layer and rejected with HTTP 403 Forbidden.
  3. The unauthorized access attempt is immediately written to the audit logs.
  4. MQTT command topics (`farm/+/device/+/command`) require broker authentication and are segregated by ACLs.

#### Threat 3: False Environmental Data
- **Threat Vector**: A malfunctioning or compromised sensor sends impossible values (e.g. 999999°C or -50% humidity) to trick automated rules into destructive actions.
- **Countermeasure**:
  1. Strict Physical Boundary Check:
     - Soil Moisture: 0.0% – 100.0%
     - Temperature: -10.0°C – 60.0°C
     - Humidity: 0.0% – 100.0%
     - Water Level: 0.0% – 100.0%
  2. Statistical Rate-of-Change Anomaly Check:
     - Temperature jumps > 25°C between consecutive readings are flagged and rejected.
     - Soil moisture jumps > 40% are flagged as sudden anomalies.
  3. Rejections trigger an `ENVIRONMENTAL` warning alert and `FALSE_DATA_DETECTED` audit record.

#### Threat 4: Availability Attacks (DoS / Brute Force)
- **Threat Vector**: Flooding the REST API or MQTT broker with requests to exhaust system resources or brute force passwords.
- **Countermeasure**:
  1. API rate limiting via SlowAPI (10 req/min on login, 120 req/min globally).
  2. Actuator continuous runtime watchdog (maximum runtime of 600s before automatic cutoff).
  3. Sensor timeout watchdog (identifies sensors that have gone offline for >60s).
  4. Container resource limits (`cpu` and `memory` bounds) in Docker and Kubernetes.

#### Threat 5: Compromised / Revoked Devices
- **Threat Vector**: A physical node is tampered with in the field.
- **Countermeasure**:
  1. Administrators can immediately **SUSPEND** the device via the Admin Panel or API.
  2. Once suspended, the backend drops all further data and logs security alerts.
