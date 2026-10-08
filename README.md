# Smart Agriculture Monitoring System (Secure IoT Platform)
### Secure Software Engineering End Semester Laboratory Project

![CI/CD Pipeline](https://github.com/secure-iot/smart-agriculture/actions/workflows/ci-cd.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![React Version](https://img.shields.io/badge/react-18.3-cyan)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-emerald)
![Security-Scan](https://img.shields.io/badge/Bandit-Passed%20(0%20High)-brightgreen)
![Vulnerability-Audit](https://img.shields.io/badge/pip--audit-0%20Vulnerabilities-brightgreen)
![Tests](https://img.shields.io/badge/pytest-28%20Passed-success)

---

## 1. Executive Summary & Overview

The **Smart Agriculture Monitoring System** is a production-grade, secure IoT agricultural platform designed to monitor environmental conditions, automate precision irrigation, and control greenhouse climate equipment while enforcing strict cybersecurity controls.

The system addresses the 6 core IoT threat vectors explicitly identified in the problem statement:
1. **Sensor Spoofing**
2. **Unauthorized Actuator Control**
3. **False Environmental Data**
4. **Availability & Resource Exhaustion Attacks**
5. **Device Identity & Cryptographic Authentication**
6. **Secure Cloud-to-Device Communication**

---

## 2. Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons
- **Backend API**: Python (FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn)
- **Database**: PostgreSQL 16 (Production / Docker) & SQLite (Zero-dependency development)
- **IoT Messaging**: Eclipse Mosquitto 2.0 MQTT Broker (Topic-level ACLs & Pre-Shared Device Keys)
- **IoT Simulator**: Python-based multi-sensor & actuator telemetry engine
- **Authentication**: JWT (HS256) via `pyjwt[crypto]`, Password hashing via `bcrypt` (12 rounds)
- **Rate Limiting**: SlowAPI (Token bucket / IP-based limiting)
- **Testing**: Pytest, HTTPX, Hypothesis (Property-based fuzzing)
- **Security Tooling**: Bandit (AST security analysis), Ruff (Linter & rules), pip-audit (Supply chain audit)
- **Containerization**: Docker, Docker Compose (Multi-stage non-root containers)
- **Orchestration**: Kubernetes (Deployments, Services, Secrets, ConfigMaps, Probes, Least Privilege Contexts)
- **CI/CD**: GitHub Actions

---

## 3. High-Level Architecture

```
                    SMART AGRICULTURE SYSTEM

                         React Frontend
                              |
                            HTTPS
                              |
                              v
                       FastAPI Backend
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
     PostgreSQL          MQTT Broker          Security/
                                             Audit Layer
                              |
                              v
                    IoT Device Simulator
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        Sensor Devices   Actuators        Greenhouse
                                             Equipment
```

---

## 4. Requirements Traceability Matrix

| Requirement | Feature / API | Database Entity | Security Control | Test Verification |
|-------------|---------------|-----------------|------------------|-------------------|
| **IoT Sensor Monitoring** | `GET /api/sensors` | `SensorReading`, `Device` | Pydantic validation, physical boundary checking | `tests/unit/test_validation.py` |
| **Environmental Monitoring** | `GET /api/sensors/{id}/readings` | `SensorReading` | Freshness check (replay mitigation) | `tests/unit/test_validation.py` |
| **Automatic Irrigation** | `ThresholdEngine._evaluate_irrigation` | `Threshold`, `Actuator` | Water-level safety interlock & runtime cutoff | `tests/unit/test_thresholds.py` |
| **Water Pump Control** | `POST /api/actuators/{id}/command` | `ActuatorCommand`, `Actuator` | Backend RBAC (`ADMIN`, `OPERATOR`) | `tests/security/test_unauthorized_actuator.py` |
| **Greenhouse Equipment** | `ThresholdEngine._evaluate_temperature` | `Actuator` | High-temp fan trigger, low-temp heater trigger | `tests/unit/test_thresholds.py` |
| **Weather Information** | `GET /api/weather` | Dynamic / OpenWeatherMap | Environmental physics simulation fallback | `tests/security/test_availability.py` |
| **Admin Thresholds** | `PUT /api/thresholds/{farm_id}` | `Threshold` | Admin RBAC check, logical range validation | `tests/unit/test_thresholds.py` |
| **Authentication** | `POST /api/auth/login` | `User` | Bcrypt hash, HS256 JWT, rate limiting | `tests/unit/test_auth.py` |
| **Role-Based Access Control** | `backend/app/core/security.py` | `User.role` | Controller-level RBAC (`require_role`) | `tests/security/test_unauthorized_actuator.py` |
| **Device Authentication** | `SensorDataValidationService` | `Device.auth_token_hash` | SHA-256 pre-shared key, constant-time HMAC | `tests/unit/test_validation.py` |
| **Sensor Spoofing Protection** | `SensorDataValidationService` | `Device`, `AuditLog` | Unregistered device rejection & critical alert | `tests/security/test_spoofing.py` |
| **False Environmental Data** | `SensorDataValidationService` | `SensorReading`, `AuditLog` | Physical bounds check & jump anomaly detector | `tests/security/test_false_data.py` |
| **Availability Protection** | `backend/app/core/limiter.py` | In-memory limiter, Watchdog | SlowAPI rate limiter, watchdog timeouts, probes | `tests/security/test_availability.py` |
| **Cloud-to-Device Security** | `backend/app/services/mqtt_service.py` | Mosquitto ACLs | Authenticated MQTT, topic-device isolation | `tests/integration/test_mqtt_pipeline.py` |
| **Audit Logging** | `GET /api/audit-logs` | `AuditLog` | Tamper-evident immutable event recording | `tests/e2e/test_e2e_scenario.py` |
| **Device Suspension** | `POST /api/devices/{id}/suspend` | `Device.status` | Immediate telemetry drop & security warning | `tests/security/test_device_suspension.py` |
| **Fuzzing Resilience** | Ingestion pipeline | `SensorReading` | Hypothesis property-based fuzzing | `tests/fuzz/test_fuzzing.py` |

---

## 5. Quick Start Instructions

### Method 1: Local Development (Zero Docker Prerequisites)

#### 1. Setup Backend:
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start backend server (starts with SQLite dev DB and auto-seeds baseline data)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Backend will be available at `http://localhost:8000`. API documentation at `http://localhost:8000/docs`.

#### 2. Setup Frontend:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at `http://localhost:3000`.

#### 3. Run IoT Simulator:
```bash
# In another terminal:
python iot-simulator/simulator.py --loop --interval 5
```

---

### Method 2: Docker Compose Deployment

```bash
# Build all container images
docker compose build

# Start services in background
docker compose up -d

# Verify service health and statuses
docker compose ps
```

Services exposed:
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL Database**: `localhost:5432`
- **Eclipse Mosquitto MQTT**: `localhost:1883`

---

### Method 3: Kubernetes Deployment

```bash
# 1. Apply namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply configuration and secrets
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# 3. Deploy infrastructure services
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/mosquitto-deployment.yaml

# 4. Deploy application workloads
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/simulator-deployment.yaml

# 5. Verify deployment status
kubectl get pods -n agri-system
kubectl get services -n agri-system
```

---

## 6. Pre-Configured Evaluation Credentials

| Role | Username | Password | Capabilities |
|------|----------|----------|--------------|
| **ADMIN** | `admin` | `Admin@Secure2026!` | Full administrative control: configure thresholds, manage/suspend devices, control actuators, view audit logs. |
| **OPERATOR** | `operator` | `Operator@Secure2026!` | Operational control: control actuators, resolve alerts, view sensors. Cannot edit thresholds or view audit logs. |
| **VIEWER** | `viewer` | `Viewer@Secure2026!` | Read-only observation: view dashboard and sensors. Any attempt to control actuators or modify settings is blocked with 403 Forbidden. |

---

## 7. Running Tests & Security Scanners

### Run Complete Pytest Suite (28 Tests)
```bash
python -m pytest tests/ -v
```
Output:
```
====================== 28 passed in 7.98s =======================
```

### Run Static Security Analysis (Bandit)
```bash
python -m bandit -r backend/ -ll
```
Output:
```
Test results: No issues identified. (0 High, 0 Medium)
```

### Run Linter & Security Standards Check (Ruff)
```bash
python -m ruff check backend/ tests/
```
Output:
```
All checks passed!
```

### Run Dependency Vulnerability Audit (pip-audit)
```bash
python -m pip_audit -r backend/requirements.txt
```
Output:
```
No known vulnerabilities found
```

---

## 8. Examination Demonstration Scenarios

Please refer to [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md) for full scenario commands and expected outputs:
- **DEMO 1**: Normal Environmental Monitoring
- **DEMO 2**: Low Soil Moisture -> Automatic Irrigation Start
- **DEMO 3**: Safe Irrigation Stop upon Target Recovery
- **DEMO 4**: Low Water Level -> Pump Safety Interlock & Emergency Shutoff
- **DEMO 5**: Sensor Spoofing -> Unregistered Device Rejection & Critical Alarm
- **DEMO 6**: False Environmental Data -> Impossible Value Rejection & Audit Log
- **DEMO 7**: Unauthorized Actuator Control -> Viewer HTTP 403 Forbidden
- **DEMO 8**: Admin Actuator Control -> Authorized Execution & Audit Record
- **DEMO 9**: Availability Protection -> Rate Limiter HTTP 429 Too Many Requests
- **DEMO 10**: Device Suspension -> Revoking Node Telemetry Privileges
