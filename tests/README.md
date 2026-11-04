# Testing and quality evidence

Automated Python tests and a broker-backed integration smoke test are committed. They test the **software MVP** only. Passing GitHub Actions does not validate hardware safety or physical motor fault classification.

## Local tests

~~~bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/check_environment.py
~~~

- [test_software_mvp.py](test_software_mvp.py): sensor JSON, features, twin state, SQLite and duplicates
- [test_real_training.py](test_real_training.py): split by independent runs, not adjacent samples
- [test_readme.py](test_readme.py): README links and Mac pull documentation
- [test_repository_quality.py](test_repository_quality.py): docs links, YAML forms, workflows and .gitignore

## End-to-end MQTT test

The [smoke test](smoke_mqtt.py) launches the live service and publishers against a separate broker on port 18884 and writes to a disposable SQLite database.

~~~bash
# Start a test broker on port 18884 first.
mosquitto -p 18884 -d
python tests/smoke_mqtt.py --port 18884
~~~

CI runs this test with a Linux Mosquitto installation. Your Mac demo uses the existing local broker on 1883 (see the [Mac runbook](../docs/MAC_RUNBOOK.md)).

## Not yet physically validated

Wokwi compilation and wiring, ESP32 Arduino compilation, current-sensor voltage scaling, NTP/real-time timestamps, physical fault data, held-out real-model metrics and the final guarded motor demonstration must be tested separately.
