source ./myenv/bin/activate

uvicorn server:app  --port 5500 --host 0.0.0.0 --reload
