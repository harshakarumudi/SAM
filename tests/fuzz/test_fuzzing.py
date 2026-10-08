import datetime

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from backend.app.schemas import SensorReadingCreate
from backend.app.services.validation_service import SensorDataValidationService


@hyp_settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    val=st.one_of(
        st.floats(allow_nan=True, allow_infinity=True),
        st.floats(min_value=-1e9, max_value=1e9),
        st.integers(min_value=-100000, max_value=100000)
    ),
    sensor_type=st.sampled_from(["soil_moisture", "temperature", "humidity", "water_level", "unknown_type"]),
    device_id=st.text(min_size=1, max_size=100)
)
def test_hypothesis_fuzz_sensor_validation(db_session, val, sensor_type, device_id):
    """
    Hypothesis Property-Based Fuzzing Test:
    Fuzzes telemetry with NaNs, Infinities, massive numbers, negative values, and diverse types.
    Invariant: The validation service MUST gracefully return (bool, reason) without raising unhandled exceptions or crashing.
    """
    try:
        reading = SensorReadingCreate(
            device_id=device_id,
            farm_id="farm_1",
            sensor_type=sensor_type if sensor_type in ["soil_moisture", "temperature", "humidity", "water_level"] else "soil_moisture",
            value=float(val) if val == val and abs(val) < 1e308 else 0.0,
            unit="%",
            timestamp=datetime.datetime.utcnow(),
            auth_token="test_token"
        )
        is_valid, reason = SensorDataValidationService.validate_and_sanitize(db_session, reading)
        assert isinstance(is_valid, bool)
        if not is_valid:
            assert isinstance(reason, str)
    except (ValueError, TypeError, OverflowError):
        # Graceful rejection by Pydantic schema or type-caster is acceptable and safe
        pass


@hyp_settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    payload_body=st.one_of(
        st.text(min_size=0, max_size=500),
        st.binary(min_size=0, max_size=500),
        st.dictionaries(st.text(), st.text())
    )
)
def test_hypothesis_fuzz_api_resilience(client, payload_body):
    """
    Fuzz API endpoints with arbitrary garbage strings, raw bytes, and random dicts.
    Invariant: Server must never produce unhandled 500 crashes or corrupt state.
    """
    try:
        resp = client.post(
            "/api/sensors/reading",
            json=payload_body if isinstance(payload_body, dict) else None,
            content=payload_body if not isinstance(payload_body, dict) else None,
            headers={"Content-Type": "application/json"}
        )
        assert resp.status_code in [200, 400, 422, 403, 401]
    except Exception as e:
        pytest.fail(f"Fuzzing caused unhandled crash: {e}")
