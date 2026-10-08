#!/bin/sh
set -e

# Generate Mosquitto password file with secure device & service credentials
touch /mosquitto/config/password_file

mosquitto_passwd -b -c /mosquitto/config/password_file backend_service "${MQTT_BACKEND_PASS:-backend_secure_mqtt_pass}"
mosquitto_passwd -b /mosquitto/config/password_file sim_soil_01 "${MQTT_SOIL_PASS:-sim_soil_pass}"
mosquitto_passwd -b /mosquitto/config/password_file sim_env_01 "${MQTT_ENV_PASS:-sim_env_pass}"
mosquitto_passwd -b /mosquitto/config/password_file sim_water_01 "${MQTT_WATER_PASS:-sim_water_pass}"
mosquitto_passwd -b /mosquitto/config/password_file sim_actuator_01 "${MQTT_ACTUATOR_PASS:-sim_actuator_pass}"

chmod 0600 /mosquitto/config/password_file
chmod 0644 /mosquitto/config/acl_file

exec mosquitto -c /mosquitto/config/mosquitto.conf
