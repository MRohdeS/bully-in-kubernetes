### How to run a small flask dev-env:
These commands need to be rerun everytime an edit to the web-app has been made

1. docker build -t flask-web-app:latest .
2. docker run -p 8000:5000 flask-web-app:latest
3. Use localhost:8000 or 127.0.0.1/8000 to view website
8000:5000, maps the flask port(5000) to the exposed port from the dockerfile(8000)

##### fails to shut down
If it doesn't shut down at ctrl+c stop it in docker desktop.