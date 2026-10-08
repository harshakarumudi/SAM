# REST API Specification
## Smart Agriculture Monitoring System

### Base URL: `/api`

### 1. Authentication (`/auth`)
- **POST `/auth/login`**
  - **Description**: Authenticate user and obtain HS256 JWT bearer token.
  - **Rate Limit**: 10 requests / minute
  - **Payload**: `{"username": "admin", "password": "Admin@Secure2026!"}`
  - **Response 200**: `{"access_token": "...", "token_type": "bearer", "role": "ADMIN", "username": "admin"}`

- **POST `/auth/register`**
  - **Description**: Register a new user account.
  - **Payload**: `{"username": "new_user", "email": "user@farm.local", "password": "Password123!", "role": "VIEWER"}`

- **GET `/auth/me`**
  - **Description**: Return authenticated user profile.
  - **Headers**: `Authorization: Bearer <token>`

---

### 2. Sensors (`/sensors`)
- **GET `/sensors`**
  - **Description**: List latest telemetry readings and status badges for all active hardware nodes.
  - **Roles**: All authenticated roles.

- **GET `/sensors/{device_id}/readings`**
  - **Description**: Historical readings for a specific hardware node.

- **POST `/sensors/reading`**
  - **Description**: Telemetry ingestion endpoint with cryptographic pre-shared secret validation.
  - **Payload**: `{"device_id": "DEV_SOIL_01", "farm_id": "farm_1", "sensor_type": "soil_moisture", "value": 45.0, "unit": "%", "auth_token": "soil_secret_key_01"}`

---

### 3. Thresholds (`/thresholds`)
- **GET `/thresholds`**
  - **Description**: View current automation setpoints and safety interlock parameters.
  - **Roles**: All authenticated roles.

- **PUT `/thresholds/{farm_id}`**
  - **Description**: Update environmental trigger thresholds.
  - **Roles**: **ADMIN ONLY** (RBAC enforced).
  - **Payload**: `{"soil_moisture_min": 30.0, "soil_moisture_target": 60.0, "temperature_min": 18.0, "temperature_max": 32.0, "humidity_min": 40.0, "humidity_max": 85.0, "water_level_safe_min": 15.0, "max_pump_runtime_seconds": 600}`

---

### 4. Actuators (`/actuators`)
- **GET `/actuators`**
  - **Description**: View status (`ON` / `OFF`) and operating mode (`AUTO` / `MANUAL`) of all actuators.

- **POST `/actuators/{actuator_id}/command`**
  - **Description**: Send manual override command.
  - **Roles**: **ADMIN** and **OPERATOR** (VIEWER receives HTTP 403 Forbidden).
  - **Payload**: `{"command": "START", "reason": "Operator manual override"}`

---

### 5. Devices (`/devices`)
- **GET `/devices`**
  - **Description**: Inventory of registered IoT hardware nodes.

- **POST `/devices`**
  - **Description**: Provision and register new hardware node.
  - **Roles**: **ADMIN ONLY**.

- **POST `/devices/{device_id}/suspend`**
  - **Description**: Administratively suspend a device node (revokes data acceptance).
  - **Roles**: **ADMIN ONLY**.

- **POST `/devices/{device_id}/activate`**
  - **Description**: Reactivate a suspended device node.
  - **Roles**: **ADMIN ONLY**.

---

### 6. Alerts & Audit Logs (`/alerts`, `/audit-logs`)
- **GET `/alerts`**
  - **Description**: Retrieve active/resolved system notifications and security alarms.
  - **Query Params**: `resolved=false`, `severity=CRITICAL`

- **POST `/alerts/{alert_id}/resolve`**
  - **Description**: Mark alert as resolved.
  - **Roles**: **ADMIN** and **OPERATOR**.

- **GET `/audit-logs`**
  - **Description**: Retrieve forensic audit logs.
  - **Roles**: **ADMIN ONLY** (Strictly forbidden to Viewer and Operator).
  - **Query Params**: `limit=100`, `severity=CRITICAL`, `event_type=SENSOR_SPOOF_ATTEMPT`

---

### 7. Health Check (`/health`)
- **GET `/health`**
  - **Description**: Container liveness/readiness probe reporting database, MQTT, and system status.
  - **Response 200**: `{"status": "healthy", "database": "connected", "mqtt": "connected", "active_devices_count": 6, "active_alerts_count": 0}`
