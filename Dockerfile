# Set base image (host OS)

FROM python:3.9.7-alpine

# By default, listen on poert 5000

EXPOSE 5000/tcp

# Set workin directory

WORKDIR /python-weather-docker

# Copy the dependencies files to the working directory

COPY requirements.txt  requirements.txt

# Install libraries and dependencies
RUN pip install -r requirements.txt

# copy content of local src directory to the working directory
COPY . .

# Specify the command to run on container start
CMD ["python3", "-m", "flask", "run"]

