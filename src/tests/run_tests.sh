#!/bin/bash
set -e
echo "Running Hawk Logger integration tests..."

# Export AWS profile (adjust as needed)
export AWS_PROFILE=hawk-logger-dev

# Invoke each test event
echo "Executing: 01_register_a_bird.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/01_register_a_bird.json
echo
echo "Executing: 02_log_food_update.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/02_log_food_update.json
echo
echo "Executing: 03_log_weight_update.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/03_log_weight_update.json
echo
echo "Executing: 04_query_missing_fields.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/04_query_missing_fields.json
echo
echo "Executing: 05_query_all_birds.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/05_query_all_birds.json
echo
echo "Executing: 06_delete_bird.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/06_delete_bird.json
echo
echo "Executing: 07_update_deleted_bird.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/07_update_deleted_bird.json
echo
echo "Executing: 08_update_unregistered_bird.json"
sam local invoke HawkLoggerFunction -e /mnt/data/hawk_logger_test_events/08_update_unregistered_bird.json
echo

echo "To verify MongoDB manually, connect and check these collections:"
echo " - db.bird_logs.find().pretty()"
echo " - db.birds.find().pretty()"