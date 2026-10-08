import os
import sys
import time
import json
import random
import logging
import argparse
import datetime
from typing import Optional
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [IoT-Simulator] %(message)s")
logger = logging.getLogger("Simulator")

# Environment configurations
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api")

# Device Pre-Shared Secrets
DEVICE_CREDENTIALS = {
    "DEV_SOIL_01": {"token": "soil_secret_key_01", "user": "sim_soil_01", "pass": "sim_soil_pass"},
    "DEV_ENV_01": {"token": "env_secret_key_01", "user": "sim_env_01", "pass": "sim_env_pass"},
    "DEV_WATER_01": {"token": "water_secret_key_01", "user": "sim_water_01", "pass": "sim_water_pass"},
    "ACT_PUMP_01": {"token": "pump_secret_key_01", "user": "sim_actuator_01", "pass": "sim_actuator_pass"},
    "ACT_FAN_01": {"token": "fan_secret_key_01", "user": "sim_actuator_01", "pass": "sim_actuator_pass"},
    "ACT_HEATER_01": {"token": "heater_secret_key_01", "user": "sim_actuator_01", "pass": "sim_actuator_pass"},
}


class IoTSimulator:
    def __init__(self, broker_host: str = MQTT_BROKER_HOST, broker_port: int = MQTT_BROKER_PORT):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.clients = {}
        self.actuator_states = {
            "ACT_PUMP_01": "OFF",
            "ACT_FAN_01": "OFF",
            "ACT_HEATER_01": "OFF"
        }
        self.running = True

        # Sensor baseline state
        self.soil_moisture = 45.0
        self.temperature = 24.0
        self.humidity = 60.0
        self.water_level = 80.0

    def init_mqtt_clients(self):
        """Initializes separate MQTT clients for each device to model distinct physical nodes."""
        for dev_id, creds in DEVICE_CREDENTIALS.items():
            try:
                try:
                    c = mqtt.Client(
                        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                        client_id=f"client_{dev_id}"
                    )
                except (AttributeError, TypeError):
                    c = mqtt.Client(client_id=f"client_{dev_id}")

                c.username_pw_set(creds["user"], creds["pass"])

                # Attach actuator callback for commands
                if dev_id.startswith("ACT_"):
                    c.on_message = self._on_actuator_command

                c.connect_async(self.broker_host, self.broker_port, 60)
                c.loop_start()

                if dev_id.startswith("ACT_"):
                    # Subscribe to actuator commands
                    c.subscribe(f"farm/farm_1/device/{dev_id}/command", qos=1)

                self.clients[dev_id] = c
            except Exception as e:
                logger.warning(f"Could not connect MQTT client for {dev_id}: {e}")

    def _on_actuator_command(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            device_id = payload.get("device_id")
            command = payload.get("command")
            logger.info(f"Actuator {device_id} RECEIVED command: {command}")

            # Update simulated state
            if command == "START":
                self.actuator_states[device_id] = "ON"
            elif command == "STOP":
                self.actuator_states[device_id] = "OFF"

            # Publish Execution ACK back to Cloud
            ack_topic = f"farm/farm_1/device/{device_id}/ack"
            ack_payload = json.dumps({
                "device_id": device_id,
                "status": self.actuator_states.get(device_id, "UNKNOWN"),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "execution": "SUCCESS"
            })
            client.publish(ack_topic, ack_payload, qos=1)
            logger.info(f"Published execution ACK on {ack_topic}: {ack_payload}")
        except Exception as e:
            logger.error(f"Error handling actuator command: {e}")

    def publish_sensor_reading(
        self,
        device_id: str,
        sensor_type: str,
        value: float,
        unit: str,
        auth_token: Optional[str] = None,
        override_topic: Optional[str] = None
    ) -> bool:
        """Publishes sensor reading via MQTT or direct fallback."""
        creds = DEVICE_CREDENTIALS.get(device_id, {})
        token = auth_token or creds.get("token", "unregistered_token")

        topic = override_topic or f"farm/farm_1/device/{device_id}/sensor"
        payload = {
            "device_id": device_id,
            "farm_id": "farm_1",
            "sensor_type": sensor_type,
            "value": round(value, 2),
            "unit": unit,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "auth_token": token
        }

        client = self.clients.get(device_id)
        if client and client.is_connected():
            res = client.publish(topic, json.dumps(payload), qos=1)
            logger.info(f"MQTT Publish [{topic}]: {sensor_type}={value}{unit}")
            return res.rc == mqtt.MQTT_ERR_SUCCESS
        else:
            # Fallback to direct HTTP endpoint if MQTT broker is currently unreachable
            import requests
            try:
                resp = requests.post(
                    f"{BACKEND_API_URL}/sensors/reading",
                    json=payload,
                    timeout=3.0
                )
                logger.info(f"HTTP Ingestion Fallback [{device_id}]: HTTP {resp.status_code}")
                return resp.status_code == 200
            except Exception as e:
                logger.debug(f"Telemetry transmit failed: {e}")
                return False

    # -------------------------------------------------------------
    # DEMONSTRATION SCENARIO HANDLERS
    # -------------------------------------------------------------
    def run_normal_monitoring_step(self):
        """Simulates normal slight agricultural variance"""
        # Dynamic soil moisture effect based on pump state
        if self.actuator_states.get("ACT_PUMP_01") == "ON":
            self.soil_moisture = min(75.0, self.soil_moisture + 3.0)
            self.water_level = max(5.0, self.water_level - 1.0)
        else:
            self.soil_moisture = max(20.0, self.soil_moisture - 0.2)

        # Dynamic temperature effect based on fan / heater state
        if self.actuator_states.get("ACT_FAN_01") == "ON":
            self.temperature = max(20.0, self.temperature - 1.0)
        elif self.actuator_states.get("ACT_HEATER_01") == "ON":
            self.temperature = min(35.0, self.temperature + 1.0)
        else:
            self.temperature += random.uniform(-0.3, 0.3)

        self.humidity += random.uniform(-0.5, 0.5)

        self.publish_sensor_reading("DEV_SOIL_01", "soil_moisture", self.soil_moisture, "%")
        self.publish_sensor_reading("DEV_ENV_01", "temperature", self.temperature, "°C")
        self.publish_sensor_reading("DEV_ENV_01", "humidity", self.humidity, "%")
        self.publish_sensor_reading("DEV_WATER_01", "water_level", self.water_level, "%")

    def run_scenario_dry_soil(self):
        """DEMO 2: Soil moisture falls below threshold (e.g. 18%), triggering auto-irrigation"""
        logger.info(">>> RUNNING SCENARIO: DRY SOIL (Soil moisture drops to 18%)")
        self.soil_moisture = 18.0
        self.publish_sensor_reading("DEV_SOIL_01", "soil_moisture", self.soil_moisture, "%")

    def run_scenario_safe_stop(self):
        """DEMO 3: Soil moisture reaches target safe level (e.g. 65%), stopping irrigation"""
        logger.info(">>> RUNNING SCENARIO: SOIL MOISTURE RECOVERY (Soil moisture rises to 65%)")
        self.soil_moisture = 65.0
        self.publish_sensor_reading("DEV_SOIL_01", "soil_moisture", self.soil_moisture, "%")

    def run_scenario_low_water(self):
        """DEMO 4: Water level drops below safe minimum (8%), triggering pump interlock"""
        logger.info(">>> RUNNING SCENARIO: LOW WATER LEVEL (Reservoir drops to 8%)")
        self.water_level = 8.0
        self.publish_sensor_reading("DEV_WATER_01", "water_level", self.water_level, "%")

    def run_scenario_sensor_spoofing(self):
        """DEMO 5: Unauthorized rogue device attempts to publish sensor data"""
        logger.info(">>> RUNNING SCENARIO: SENSOR SPOOFING (Unregistered device DEV_ROGUE_99)")
        payload = {
            "device_id": "DEV_ROGUE_99",
            "farm_id": "farm_1",
            "sensor_type": "soil_moisture",
            "value": 10.0,
            "unit": "%",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "auth_token": "fake_unauthorized_token"
        }
        # Attempt to publish via rogue HTTP or MQTT
        import requests
        try:
            resp = requests.post(f"{BACKEND_API_URL}/sensors/reading", json=payload, timeout=3.0)
            logger.info(f"Spoofing attempt response: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Spoofing request error: {e}")

    def run_scenario_false_data(self):
        """DEMO 6: Impossible sensor values (e.g., 999°C or -50% humidity)"""
        logger.info(">>> RUNNING SCENARIO: FALSE ENVIRONMENTAL DATA (Temperature = 999°C)")
        self.publish_sensor_reading("DEV_ENV_01", "temperature", 999.0, "°C")

    def run_scenario_high_temp(self):
        """Greenhouse heat stress -> Fan auto start"""
        logger.info(">>> RUNNING SCENARIO: HIGH GREENHOUSE TEMP (38°C)")
        self.temperature = 38.0
        self.publish_sensor_reading("DEV_ENV_01", "temperature", self.temperature, "°C")

    def run_loop(self, interval_seconds: int = 5):
        """Continuous simulation loop for long-running monitoring"""
        logger.info(f"Starting IoT simulator loop (interval={interval_seconds}s)...")
        self.init_mqtt_clients()
        time.sleep(1)

        while self.running:
            try:
                self.run_normal_monitoring_step()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Simulator stopped by user.")
                break
            except Exception as e:
                logger.error(f"Simulator error in loop: {e}")
                time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure IoT Agriculture Simulator")
    parser.add_argument("--scenario", choices=["normal", "dry_soil", "safe_stop", "low_water", "spoofing", "false_data", "high_temp"], default="normal")
    parser.add_argument("--loop", action="store_true", help="Run in continuous monitoring loop")
    parser.add_argument("--interval", type=int, default=5, help="Telemetry interval in seconds")
    args = parser.parse_args()

    sim = IoTSimulator()
    sim.init_mqtt_clients()
    time.sleep(1)

    if args.scenario == "dry_soil":
        sim.run_scenario_dry_soil()
    elif args.scenario == "safe_stop":
        sim.run_scenario_safe_stop()
    elif args.scenario == "low_water":
        sim.run_scenario_low_water()
    elif args.scenario == "spoofing":
        sim.run_scenario_sensor_spoofing()
    elif args.scenario == "false_data":
        sim.run_scenario_false_data()
    elif args.scenario == "high_temp":
        sim.run_scenario_high_temp()
    elif args.loop:
        sim.run_loop(interval_seconds=args.interval)
    else:
        # Default: single normal monitoring step
        sim.run_normal_monitoring_step()
        logger.info("Single normal monitoring step complete. Use --loop for continuous simulation.")
