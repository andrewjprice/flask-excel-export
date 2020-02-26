# Flask - Celery Example

![](excel-report-generator.gif)

## Steps
1. Add AWS S3 credentials in app.py

2. Install dependencies
```
pip install -r requirements.txt (in virtualenv)
```

3. Start Redis
```
sh ./run-redis
```

4. Start Celery Worker
```
celery worker -A app.celery --loglevel=info
```

5. Run app.py
```
python app.py
```

