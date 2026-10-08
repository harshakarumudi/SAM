import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.core.limiter import limiter
from backend.app.core.security import (
    create_access_token,
    get_password_hash,
    hash_device_token,
)
from backend.app.main import app
from backend.app.models import Actuator, Device, Farm, Threshold, User


@pytest.fixture(autouse=True)
def reset_limiter_fixture():
    try:
        limiter.reset()
    except Exception:
        pass

# In-memory test database with static pool for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Farm
    farm = Farm(id="farm_1", name="Test Green Farm", location="Sector Alpha")
    db.add(farm)

    # Seed Users
    admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("Admin@Secure2026!"),
        role="ADMIN",
        is_active=True
    )
    operator = User(
        username="operator",
        email="operator@test.com",
        hashed_password=get_password_hash("Operator@Secure2026!"),
        role="OPERATOR",
        is_active=True
    )
    viewer = User(
        username="viewer",
        email="viewer@test.com",
        hashed_password=get_password_hash("Viewer@Secure2026!"),
        role="VIEWER",
        is_active=True
    )
    db.add_all([admin, operator, viewer])

    # Seed Thresholds
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
        updated_by="TEST_INIT"
    )
    db.add(threshold)

    # Seed Devices
    devs = [
        Device(id="DEV_SOIL_01", farm_id="farm_1", device_name="Soil Sensor", device_type="soil_moisture", status="active", auth_token_hash=hash_device_token("soil_secret_key_01")),
        Device(id="DEV_ENV_01", farm_id="farm_1", device_name="Env Sensor", device_type="environmental", status="active", auth_token_hash=hash_device_token("env_secret_key_01")),
        Device(id="DEV_WATER_01", farm_id="farm_1", device_name="Water Sensor", device_type="water_level", status="active", auth_token_hash=hash_device_token("water_secret_key_01")),
        Device(id="DEV_SUSPENDED_01", farm_id="farm_1", device_name="Suspended Sensor", device_type="soil_moisture", status="suspended", auth_token_hash=hash_device_token("suspended_secret_key")),
    ]
    db.add_all(devs)

    # Seed Actuators
    acts = [
        Actuator(id="ACT_PUMP_01", device_id="DEV_PUMP_01", farm_id="farm_1", actuator_type="pump", status="OFF", mode="AUTO"),
        Actuator(id="ACT_FAN_01", device_id="DEV_FAN_01", farm_id="farm_1", actuator_type="fan", status="OFF", mode="AUTO"),
        Actuator(id="ACT_HEATER_01", device_id="DEV_HEATER_01", farm_id="farm_1", actuator_type="heater", status="OFF", mode="AUTO"),
    ]
    db.add_all(acts)

    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "role": "ADMIN"})


@pytest.fixture
def operator_token():
    return create_access_token({"sub": "operator", "role": "OPERATOR"})


@pytest.fixture
def viewer_token():
    return create_access_token({"sub": "viewer", "role": "VIEWER"})
