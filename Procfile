web: gunicorn app:app --bind 0.0.0.0:$PORT
worker: python sam_gov_scanner.py && python alert_generator.py
