start ngrok.exe http 5000
start rasa run --enable-api -p 5000
start rasa run actions
start docker run -p 8000:8000 rasa/duckling
