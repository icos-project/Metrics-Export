# Use the official Python 3.11 image as the base image
FROM python:3.11
USER root

# Set the working directory in the container
WORKDIR /usr/src/

# Copy the dependencies file to the container
COPY requirements.txt .

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Use an entrypoint script to start Gunicorn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
