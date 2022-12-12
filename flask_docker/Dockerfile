# Using official python runtime base image
FROM python:3.10

# Set the app directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements to container and install
#COPY requirements.txt requirements.txt
#RUN pip install -r requirements.txt
 
RUN pip install -U Flask

# Upgrade pip
RUN pip install --upgrade pip

# Copy all to current dir
COPY . .

#Expose port 5000 for webapp due to flask
EXPOSE 5000

# This will print python logs to output
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Define the command to be run when launching the container
CMD ["python", "./web_app.py"]