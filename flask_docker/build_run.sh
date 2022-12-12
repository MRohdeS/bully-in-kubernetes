#!/bin/bash
docker build -t flask-web-app:latest
docker run -p 8000:5000 flask-web-app:latest
