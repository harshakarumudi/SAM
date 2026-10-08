# System Architecture Document
## Smart Agriculture Monitoring System (Secure IoT Platform)

### 1. High-Level Architecture Overview

The Smart Agriculture Monitoring System is an end-to-end, defense-in-depth IoT platform engineered for high-assurance environmental monitoring, safety-critical actuator automation, and cryptographic access control.

```
+-----------------------------------------------------------------------+
|                           REACT DASHBOARD                             |
|        (Vite + TypeScript + Tailwind CSS + Responsive RBAC Views)     |
+-----------------------------------------------------------------------+
                                    |
                             HTTPS / JSON REST
                                    |
                                    v
+-----------------------------------------------------------------------+
|                           FASTAPI BACKEND                             |
|  - JWT Authentication & RBAC Engine (ADMIN, OPERATOR, VIEWER)         |
|  - Rate Limiter (SlowAPI / Token Bucket)                              |
|  - Sensor Validation & Anti-Spoofing Service                          |
|  - Threshold & Automation Rules Engine with Safety Interlocks         |
|  - Watchdog Engine (Sensor Loss of Signal & Max Runtime Cutoff)       |
|  - Tamper-Evident Audit Logging Subsystem                             |
+-----------------------------------------------------------------------+
          |                                  |
          | SQL Alchemy                      | Authenticated MQTT (paho-mqtt)
          v                                  v
+--------------------+            +------------------------------------+
|    POSTGRESQL /    |            |       MOSQUITTO MQTT BROKER        |
|    SQLITE DB       |            |  - Topic ACL Enforcement           |
| (Users, Readings,  |            |  - Cryptographic Device Auth       |
|  Devices, Alerts,  |            |  - farm/{id}/device/{id}/sensor    |
|  Audit Logs)       |            |  - farm/{id}/device/{id}/command   |
+--------------------+            +------------------------------------+
                                             |
                                  MQTT Mutual Isolation
                                             v
                          +------------------------------------+
                          |        IOT DEVICE SIMULATOR        |
                          |  - Soil Moisture Sensor (DEV_SOIL) |
                          |  - Climate Node (DEV_ENV_01)       |
                          |  - Water Level Node (DEV_WATER_01) |
                          |  - Actuator Node (ACT_PUMP/FAN/HTR)|
                          +------------------------------------+
```

### 2. Core Subsystems

#### 2.1 Backend / API Subsystem
- **Framework**: FastAPI (Asynchronous Python 3.12/3.13)
- **Data Validation**: Pydantic v2 strict typing and boundary validation.
- **ORM & Data Layer**: SQLAlchemy 2.0 with connection pooling and migrations.
- **Security Protocols**: PBKDF2/bcrypt hashing, HS256 JWT tokens, constant-time HMAC token comparisons.

#### 2.2 Broker & IoT Ingestion Pipeline
- **Broker**: Eclipse Mosquitto v2.0
- **Access Control Lists (ACL)**: Restricts devices strictly to their provisioned topic trees:
  - `farm/{farm_id}/device/{device_id}/sensor` (Write only by matching hardware node)
  - `farm/{farm_id}/device/{device_id}/command` (Read only by matching actuator)
  - `farm/{farm_id}/device/{device_id}/ack` (Write execution receipt)
  - `farm/#` (Read/Write reserved exclusively for Backend Core Service)

#### 2.3 Automation & Safety Interlock Engine
- **Irrigation Logic**:
  - Automatically starts irrigation when Soil Moisture < configured minimum.
  - Automatically cuts off pump when Soil Moisture reaches safe target.
  - **Water Level Safety Interlock**: If the water reservoir drops below the safety cutoff (15%), the pump is hard-locked from starting to avoid dry-run burnouts. If running, it immediately emergency-shuts down.
  - **Maximum Runtime Cutoff**: Watchdog monitors continuous pump operation. If runtime exceeds 600s (10m), the pump is automatically halted and an alarm is raised.
- **Greenhouse Climate Control**:
  - Activates high-volume exhaust fans when temperature > upper threshold (32°C) or humidity > 85%.
  - Activates radiant heater when temperature < lower threshold (18°C).

#### 2.4 Device Authentication & Revocation
- Every device node is registered with a unique cryptographic pre-shared secret.
- Nodes can be administratively **SUSPENDED**. Once suspended, the backend validation pipeline immediately drops incoming telemetry and issues a security alarm.
