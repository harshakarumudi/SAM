import datetime
import logging
import threading
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.api.v1.actuators import router as actuators_router
from backend.app.api.v1.alerts import router as alerts_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.devices import router as devices_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.sensors import router as sensors_router
from backend.app.api.v1.thresholds import router as thresholds_router
from backend.app.api.v1.weather import router as weather_router
from backend.app.core.config import settings
from backend.app.core.database import Base, SessionLocal, engine
from backend.app.core.limiter import limiter
from backend.app.core.security import get_password_hash, hash_device_token
from backend.app.models import Actuator, Alert, Device, Farm, Threshold, User
from backend.app.services.audit_service import log_security_event
from backend.app.services.mqtt_service import mqtt_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SmartAgriBackend")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Secure IoT-based Agricultural Monitoring and Automation Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None
)

# Attach SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows browser frontend communication in development/docker
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global secure error handling to prevent sensitive information disclosure
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    # Never leak stack traces, database schema, or internal errors in responses
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. The incident has been recorded."}
    )


# Include API Routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(sensors_router, prefix=settings.API_V1_STR)
app.include_router(thresholds_router, prefix=settings.API_V1_STR)
app.include_router(actuators_router, prefix=settings.API_V1_STR)
app.include_router(devices_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(weather_router, prefix=settings.API_V1_STR)


def seed_database():
    """Initializes schema and seeds baseline users, farm, devices, and thresholds"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Farm
        farm = db.query(Farm).filter(Farm.id == "farm_1").first()
        if not farm:
            farm = Farm(
                id="farm_1",
                name="Green Valley Smart Farm",
                location="Sector 4B, Agricultural Zone",
                description="Automated IoT Precision Agriculture Facility"
            )
            db.add(farm)
            db.commit()

        # 2. Seed Default Users (ADMIN, OPERATOR, VIEWER)
        users = [
            ("admin", "admin@agri-secure.local", "Admin@Secure2026!", "ADMIN"),
            ("operator", "operator@agri-secure.local", "Operator@Secure2026!", "OPERATOR"),
            ("viewer", "viewer@agri-secure.local", "Viewer@Secure2026!", "VIEWER"),
        ]
        for uname, email, pwd, role in users:
            existing_user = db.query(User).filter(User.username == uname).first()
            if not existing_user:
                u = User(
                    username=uname,
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    role=role,
                    is_active=True
                )
                db.add(u)
        db.commit()

        # 3. Seed Thresholds
        threshold = db.query(Threshold).filter(Threshold.farm_id == "farm_1").first()
        if not threshold:
            threshold = Threshold(
                farm_id="farm_1",
                soil_moisture_min=30.0,
                soil_moisture_target=60.0,
                temperature_min=18.0,
                temperature_max=32.0,
                humidity_min=40.0,
                humidity_max=85.0,
                water_level_safe_min=15.0,
                max_pump_runtime_seconds=600,
                updated_by="SYSTEM_INIT"
            )
            db.add(threshold)
            db.commit()

        # 4. Seed Registered Devices with pre-shared tokens
        devices = [
            ("DEV_SOIL_01", "Soil Moisture Sensor Alpha", "soil_moisture", "soil_secret_key_01"),
            ("DEV_ENV_01", "Greenhouse Climate Sensor Alpha", "environmental", "env_secret_key_01"),
            ("DEV_WATER_01", "Main Water Reservoir Level Sensor", "water_level", "water_secret_key_01"),
            ("DEV_PUMP_01", "Irrigation Submersible Pump Controller", "actuator", "pump_secret_key_01"),
            ("DEV_FAN_01", "Greenhouse Ventilation Fan Controller", "actuator", "fan_secret_key_01"),
            ("DEV_HEATER_01", "Greenhouse Radiant Heater Controller", "actuator", "heater_secret_key_01"),
        ]
        for dev_id, name, dtype, token in devices:
            dev = db.query(Device).filter(Device.id == dev_id).first()
            if not dev:
                dev = Device(
                    id=dev_id,
                    farm_id="farm_1",
                    device_name=name,
                    device_type=dtype,
                    status="active",
                    auth_token_hash=hash_device_token(token),
                    last_seen=datetime.datetime.utcnow(),
                    created_at=datetime.datetime.utcnow()
                )
                db.add(dev)
        db.commit()

        # 5. Seed Actuators
        actuators = [
            ("ACT_PUMP_01", "DEV_PUMP_01", "pump"),
            ("ACT_FAN_01", "DEV_FAN_01", "fan"),
            ("ACT_HEATER_01", "DEV_HEATER_01", "heater"),
        ]
        for act_id, dev_id, atype in actuators:
            act = db.query(Actuator).filter(Actuator.id == act_id).first()
            if not act:
                act = Actuator(
                    id=act_id,
                    device_id=dev_id,
                    farm_id="farm_1",
                    actuator_type=atype,
                    status="OFF",
                    mode="AUTO"
                )
                db.add(act)
        db.commit()

        logger.info("Database schema verified and initial baseline seeds created.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


# Availability & Safety Watchdog Thread
def availability_watchdog_loop():
    """
    Background Watchdog:
    1. Detects offline/unresponsive sensors (Availability Protection).
    2. Enforces maximum pump runtime cutoff to protect physical equipment.
    """
    logger.info("Starting Availability Watchdog thread...")
    while True:
        try:
            time.sleep(15)  # Run periodic scan every 15 seconds
            db = SessionLocal()
            now = datetime.datetime.utcnow()

            # 1. Sensor Watchdog: Check for inactive active sensors
            devices = db.query(Device).filter(
                Device.status == "active",
                Device.device_type.in_(["soil_moisture", "environmental", "water_level"])
            ).all()

            for dev in devices:
                if dev.last_seen:
                    elapsed = (now - dev.last_seen).total_seconds()
                    if elapsed > settings.SENSOR_WATCHDOG_TIMEOUT_SECONDS:
                        # Sensor is overdue, raise availability alert
                        existing_alert = db.query(Alert).filter(
                            Alert.device_id == dev.id,
                            Alert.category == "AVAILABILITY",
                            Alert.resolved == False
                        ).first()
                        if not existing_alert:
                            alert = Alert(
                                farm_id=dev.farm_id,
                                device_id=dev.id,
                                severity="WARNING",
                                category="AVAILABILITY",
                                title="Sensor Offline Detected",
                                message=f"Sensor '{dev.id}' has not sent telemetry in {int(elapsed)} seconds."
                            )
                            db.add(alert)
                            log_security_event(
                                db=db,
                                event_type="SENSOR_TIMEOUT_DETECTED",
                                actor_type="SYSTEM",
                                actor_id="WATCHDOG",
                                action="AVAILABILITY_CHECK",
                                resource=f"device:{dev.id}",
                                result="WARNING",
                                severity="WARNING",
                                details=f"Sensor elapsed time: {int(elapsed)}s"
                            )
                            db.commit()

            # 2. Actuator Runtime Safety Check: Cut off pump if running too long
            pump = db.query(Actuator).filter(Actuator.actuator_type == "pump", Actuator.status == "ON").first()
            if pump and pump.last_activated_at:
                runtime = (now - pump.last_activated_at).total_seconds()
                pump.current_runtime_seconds = int(runtime)
                if runtime > settings.MAX_PUMP_RUNTIME_SECONDS:
                    pump.status = "OFF"
                    pump.last_deactivated_at = now
                    alert = Alert(
                        farm_id=pump.farm_id,
                        device_id=pump.device_id,
                        severity="CRITICAL",
                        category="EQUIPMENT",
                        title="Maximum Pump Runtime Exceeded - Automatic Cutoff",
                        message=f"Pump operated continuously for {int(runtime)}s exceeding maximum limit of {settings.MAX_PUMP_RUNTIME_SECONDS}s. Forcefully stopped."
                    )
                    db.add(alert)
                    log_security_event(
                        db=db,
                        event_type="MAX_RUNTIME_EXCEEDED_SHUTDOWN",
                        actor_type="SYSTEM",
                        actor_id="WATCHDOG",
                        action="FORCE_SHUTDOWN",
                        resource=f"actuator:{pump.id}",
                        result="SUCCESS",
                        severity="CRITICAL",
                        details=f"Runtime: {int(runtime)}s"
                    )
                    db.commit()
                    # Dispatch stop command to hardware
                    mqtt_manager.publish_actuator_command(pump.farm_id, pump.device_id, "STOP")
                else:
                    db.commit()

            db.close()
        except Exception as e:
            logger.error(f"Error in watchdog loop: {e}")


@app.on_event("startup")
def on_startup():
    seed_database()
    mqtt_manager.start()
    watchdog_thread = threading.Thread(target=availability_watchdog_loop, daemon=True)
    watchdog_thread.start()


@app.on_event("shutdown")
def on_shutdown():
    mqtt_manager.stop()
