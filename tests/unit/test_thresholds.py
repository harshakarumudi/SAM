from backend.app.models import Actuator, SensorReading
from backend.app.services.threshold_engine import ThresholdEngine


def test_automatic_irrigation_start_on_dry_soil(db_session):
    """DEMO 2: When soil moisture drops below min threshold (30%), pump starts automatically"""
    pump = db_session.query(Actuator).filter(Actuator.actuator_type == "pump").first()
    pump.status = "OFF"
    db_session.commit()

    # Ensure water reservoir is safe (80%)
    water_reading = SensorReading(
        device_id="DEV_WATER_01",
        farm_id="farm_1",
        sensor_type="water_level",
        value=80.0,
        unit="%",
        is_valid=True
    )
    db_session.add(water_reading)
    db_session.commit()

    # Trigger soil moisture below min (20% < 30%)
    ThresholdEngine.evaluate(db_session, "farm_1", "soil_moisture", 20.0)

    db_session.refresh(pump)
    assert pump.status == "ON"


def test_automatic_irrigation_safe_stop(db_session):
    """DEMO 3: When soil moisture reaches target safe level (60%), pump stops automatically"""
    pump = db_session.query(Actuator).filter(Actuator.actuator_type == "pump").first()
    pump.status = "ON"
    db_session.commit()

    # Trigger soil moisture reaching target (65% >= 60%)
    ThresholdEngine.evaluate(db_session, "farm_1", "soil_moisture", 65.0)

    db_session.refresh(pump)
    assert pump.status == "OFF"


def test_low_water_level_safety_interlock(db_session):
    """DEMO 4: Water level below safe min (15%) MUST prevent pump startup and shut it down"""
    pump = db_session.query(Actuator).filter(Actuator.actuator_type == "pump").first()
    pump.status = "OFF"
    db_session.commit()

    # Inject depleted reservoir reading (8% < 15%)
    water_reading = SensorReading(
        device_id="DEV_WATER_01",
        farm_id="farm_1",
        sensor_type="water_level",
        value=8.0,
        unit="%",
        is_valid=True
    )
    db_session.add(water_reading)
    db_session.commit()

    # Attempt to trigger irrigation with dry soil
    ThresholdEngine.evaluate(db_session, "farm_1", "soil_moisture", 15.0)

    # Pump must remain locked out in OFF state
    db_session.refresh(pump)
    assert pump.status == "OFF"


def test_greenhouse_fan_high_temperature(db_session):
    """High temperature above 32°C activates cooling fan"""
    fan = db_session.query(Actuator).filter(Actuator.actuator_type == "fan").first()
    fan.status = "OFF"
    db_session.commit()

    # 36°C > 32°C
    ThresholdEngine.evaluate(db_session, "farm_1", "temperature", 36.0)

    db_session.refresh(fan)
    assert fan.status == "ON"


def test_greenhouse_heater_low_temperature(db_session):
    """Low temperature below 18°C activates radiant heater"""
    heater = db_session.query(Actuator).filter(Actuator.actuator_type == "heater").first()
    heater.status = "OFF"
    db_session.commit()

    # 12°C < 18°C
    ThresholdEngine.evaluate(db_session, "farm_1", "temperature", 12.0)

    db_session.refresh(heater)
    assert heater.status == "ON"
