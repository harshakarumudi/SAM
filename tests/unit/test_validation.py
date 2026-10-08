import datetime

from backend.app.schemas import SensorReadingCreate
from backend.app.services.validation_service import SensorDataValidationService


def test_valid_soil_moisture_reading(db_session):
    reading = SensorReadingCreate(
        device_id="DEV_SOIL_01",
        farm_id="farm_1",
        sensor_type="soil_moisture",
        value=45.5,
        unit="%",
        timestamp=datetime.datetime.utcnow(),
        auth_token="soil_secret_key_01"
    )
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
    assert is_valid is True
    assert reason is None


def test_reject_impossible_temperature_value(db_session):
    """Protection against false environmental data (e.g. 999999°C)"""
    reading = SensorReadingCreate(
        device_id="DEV_ENV_01",
        farm_id="farm_1",
        sensor_type="temperature",
        value=999.0,  # Impossible physical value
        unit="°C",
        timestamp=datetime.datetime.utcnow(),
        auth_token="env_secret_key_01"
    )
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
    assert is_valid is False
    assert "FALSE_ENVIRONMENTAL_DATA" in reason


def test_reject_negative_humidity(db_session):
    """Protection against negative humidity"""
    reading = SensorReadingCreate(
        device_id="DEV_ENV_01",
        farm_id="farm_1",
        sensor_type="humidity",
        value=-25.0,  # Negative humidity
        unit="%",
        timestamp=datetime.datetime.utcnow(),
        auth_token="env_secret_key_01"
    )
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
    assert is_valid is False
    assert "FALSE_ENVIRONMENTAL_DATA" in reason


def test_reject_stale_replay_timestamp(db_session):
    """Protection against replay attacks with expired timestamps (> 300s old)"""
    old_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=600)
    reading = SensorReadingCreate(
        device_id="DEV_SOIL_01",
        farm_id="farm_1",
        sensor_type="soil_moisture",
        value=50.0,
        unit="%",
        timestamp=old_time,
        auth_token="soil_secret_key_01"
    )
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
    assert is_valid is False
    assert "REPLAY_OR_STALE" in reason


def test_reject_future_timestamp(db_session):
    """Protection against timestamp manipulation in future"""
    future_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=120)
    reading = SensorReadingCreate(
        device_id="DEV_SOIL_01",
        farm_id="farm_1",
        sensor_type="soil_moisture",
        value=50.0,
        unit="%",
        timestamp=future_time,
        auth_token="soil_secret_key_01"
    )
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
    assert is_valid is False
    assert "FUTURE_TIMESTAMP" in reason
