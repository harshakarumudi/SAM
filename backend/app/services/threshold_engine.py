import datetime

from sqlalchemy.orm import Session

from backend.app.models import (
    Actuator,
    ActuatorCommand,
    Alert,
    SensorReading,
    Threshold,
)
from backend.app.services.audit_service import log_security_event


class ThresholdEngine:
    @staticmethod
    def get_or_create_thresholds(db: Session, farm_id: str) -> Threshold:
        threshold = db.query(Threshold).filter(Threshold.farm_id == farm_id).first()
        if not threshold:
            threshold = Threshold(
                farm_id=farm_id,
                soil_moisture_min=30.0,
                soil_moisture_target=60.0,
                temperature_min=18.0,
                temperature_max=32.0,
                humidity_min=40.0,
                humidity_max=85.0,
                water_level_safe_min=15.0,
                max_pump_runtime_seconds=600,
                updated_by="SYSTEM_DEFAULT"
            )
            db.add(threshold)
            db.commit()
            db.refresh(threshold)
        return threshold

    @classmethod
    def evaluate(cls, db: Session, farm_id: str, sensor_type: str, current_value: float):
        """
        Main rules engine evaluating environmental conditions and triggering
        automatic fail-safe actuator behaviors.
        """
        threshold = cls.get_or_create_thresholds(db, farm_id)

        if sensor_type == "soil_moisture":
            cls._evaluate_irrigation(db, farm_id, threshold, current_value)
        elif sensor_type == "water_level":
            cls._evaluate_water_level(db, farm_id, threshold, current_value)
        elif sensor_type == "temperature":
            cls._evaluate_temperature(db, farm_id, threshold, current_value)
        elif sensor_type == "humidity":
            cls._evaluate_humidity(db, farm_id, threshold, current_value)

    @classmethod
    def _evaluate_irrigation(cls, db: Session, farm_id: str, threshold: Threshold, soil_moisture: float):
        pump = db.query(Actuator).filter(
            Actuator.farm_id == farm_id,
            Actuator.actuator_type == "pump"
        ).first()
        if not pump:
            return

        # Fetch latest valid water level
        latest_water = (
            db.query(SensorReading)
            .filter(
                SensorReading.farm_id == farm_id,
                SensorReading.sensor_type == "water_level",
                SensorReading.is_valid == True
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        water_level = latest_water.value if latest_water else 50.0  # Safe default if not yet published

        # 1. Condition: Soil is dry (< configured min)
        if soil_moisture < threshold.soil_moisture_min:
            # SAFETY INTERLOCK: Water level check
            if water_level < threshold.water_level_safe_min:
                # Water is too low! Pump must NOT start.
                if pump.status == "ON":
                    cls._set_actuator_state(db, pump, "OFF", "SAFETY_INTERLOCK: Reservoir below minimum safe water level")

                alert = Alert(
                    farm_id=farm_id,
                    device_id=pump.device_id,
                    severity="CRITICAL",
                    category="EQUIPMENT",
                    title="Pump Startup Inhibited - Low Water Reservoir",
                    message=f"Dry soil detected ({soil_moisture}%), but water reservoir ({water_level}%) is below safety threshold ({threshold.water_level_safe_min}%). Pump locked out."
                )
                db.add(alert)
                log_security_event(
                    db=db,
                    event_type="SAFETY_INTERLOCK_TRIGGERED",
                    actor_type="SYSTEM",
                    actor_id="THRESHOLD_ENGINE",
                    action="INHIBIT_PUMP",
                    resource="actuator:pump",
                    result="BLOCKED",
                    severity="CRITICAL",
                    details=f"Inhibited irrigation. Soil={soil_moisture}%, WaterLevel={water_level}%"
                )
                db.commit()
                return

            # Check if pump is already running
            if pump.status == "OFF":
                cls._set_actuator_state(db, pump, "ON", f"Automatic irrigation start (Soil moisture {soil_moisture}% < {threshold.soil_moisture_min}%)")
                alert = Alert(
                    farm_id=farm_id,
                    device_id=pump.device_id,
                    severity="INFO",
                    category="EQUIPMENT",
                    title="Automatic Irrigation Activated",
                    message=f"Soil moisture dropped to {soil_moisture}%. Water pump started."
                )
                db.add(alert)
                db.commit()

        # 2. Condition: Soil reached target safe level (>= target)
        elif soil_moisture >= threshold.soil_moisture_target:
            if pump.status == "ON":
                cls._set_actuator_state(db, pump, "OFF", f"Target soil moisture achieved ({soil_moisture}% >= {threshold.soil_moisture_target}%)")
                alert = Alert(
                    farm_id=farm_id,
                    device_id=pump.device_id,
                    severity="INFO",
                    category="EQUIPMENT",
                    title="Automatic Irrigation Stopped",
                    message=f"Soil moisture reached target {soil_moisture}%. Water pump stopped safely."
                )
                db.add(alert)
                db.commit()

    @classmethod
    def _evaluate_water_level(cls, db: Session, farm_id: str, threshold: Threshold, water_level: float):
        pump = db.query(Actuator).filter(
            Actuator.farm_id == farm_id,
            Actuator.actuator_type == "pump"
        ).first()
        if not pump:
            return

        if water_level < threshold.water_level_safe_min:
            # Low water level alert
            alert = Alert(
                farm_id=farm_id,
                device_id="DEV_WATER_01",
                severity="CRITICAL",
                category="EQUIPMENT",
                title="Critical Water Reservoir Depletion",
                message=f"Water level dropped to {water_level}% (Safety minimum: {threshold.water_level_safe_min}%)."
            )
            db.add(alert)

            # If pump is running, immediate safety shutdown
            if pump.status == "ON":
                cls._set_actuator_state(db, pump, "OFF", "SAFETY_INTERLOCK: Emergency shutoff due to water depletion")
                log_security_event(
                    db=db,
                    event_type="SAFETY_INTERLOCK_SHUTDOWN",
                    actor_type="SYSTEM",
                    actor_id="THRESHOLD_ENGINE",
                    action="EMERGENCY_STOP_PUMP",
                    resource="actuator:pump",
                    result="SUCCESS",
                    severity="CRITICAL",
                    details=f"Emergency pump stop executed. WaterLevel={water_level}%"
                )
            db.commit()

    @classmethod
    def _evaluate_temperature(cls, db: Session, farm_id: str, threshold: Threshold, temperature: float):
        fan = db.query(Actuator).filter(Actuator.farm_id == farm_id, Actuator.actuator_type == "fan").first()
        heater = db.query(Actuator).filter(Actuator.farm_id == farm_id, Actuator.actuator_type == "heater").first()

        # High Temperature -> Fan ON, Heater OFF
        if temperature > threshold.temperature_max:
            if fan and fan.status == "OFF":
                cls._set_actuator_state(db, fan, "ON", f"High temp ({temperature}°C > {threshold.temperature_max}°C)")
                alert = Alert(
                    farm_id=farm_id,
                    device_id=fan.device_id,
                    severity="WARNING",
                    category="EQUIPMENT",
                    title="Greenhouse Fan Activated",
                    message=f"High temperature ({temperature}°C). Cooling fan turned ON."
                )
                db.add(alert)
            if heater and heater.status == "ON":
                cls._set_actuator_state(db, heater, "OFF", "Turned OFF heater due to high temp")

        # Low Temperature -> Heater ON, Fan OFF
        elif temperature < threshold.temperature_min:
            if heater and heater.status == "OFF":
                cls._set_actuator_state(db, heater, "ON", f"Low temp ({temperature}°C < {threshold.temperature_min}°C)")
                alert = Alert(
                    farm_id=farm_id,
                    device_id=heater.device_id,
                    severity="WARNING",
                    category="EQUIPMENT",
                    title="Greenhouse Heater Activated",
                    message=f"Low temperature ({temperature}°C). Heating system turned ON."
                )
                db.add(alert)
            if fan and fan.status == "ON":
                cls._set_actuator_state(db, fan, "OFF", "Turned OFF fan due to low temp")

        # Normal Temperature
        else:
            if heater and heater.status == "ON":
                cls._set_actuator_state(db, heater, "OFF", "Normal temp range restored")
            if fan and fan.status == "ON":
                cls._set_actuator_state(db, fan, "OFF", "Normal temp range restored")

        db.commit()

    @classmethod
    def _evaluate_humidity(cls, db: Session, farm_id: str, threshold: Threshold, humidity: float):
        fan = db.query(Actuator).filter(Actuator.farm_id == farm_id, Actuator.actuator_type == "fan").first()
        if not fan:
            return

        if humidity > threshold.humidity_max:
            if fan.status == "OFF":
                cls._set_actuator_state(db, fan, "ON", f"High humidity ventilation ({humidity}% > {threshold.humidity_max}%)")
                alert = Alert(
                    farm_id=farm_id,
                    device_id=fan.device_id,
                    severity="WARNING",
                    category="ENVIRONMENTAL",
                    title="Excess Humidity Ventilation",
                    message=f"High humidity ({humidity}%). Exhaust fan activated."
                )
                db.add(alert)
                db.commit()

    @classmethod
    def _set_actuator_state(cls, db: Session, actuator: Actuator, target_state: str, reason: str):
        now = datetime.datetime.utcnow()
        actuator.status = target_state
        actuator.updated_at = now
        if target_state == "ON":
            actuator.last_activated_at = now
            actuator.current_runtime_seconds = 0
        else:
            actuator.last_deactivated_at = now
            actuator.current_runtime_seconds = 0

        cmd = ActuatorCommand(
            actuator_id=actuator.id,
            command="START" if target_state == "ON" else "STOP",
            issuer_type="AUTO_SYSTEM",
            issuer_id="THRESHOLD_ENGINE",
            status="EXECUTED",
            reason=reason,
            timestamp=now
        )
        db.add(cmd)

        log_security_event(
            db=db,
            event_type="ACTUATOR_STATE_CHANGE",
            actor_type="SYSTEM",
            actor_id="THRESHOLD_ENGINE",
            action=f"SET_{target_state}",
            resource=f"actuator:{actuator.id}",
            result="SUCCESS",
            severity="INFO",
            details=reason
        )
        db.commit()
