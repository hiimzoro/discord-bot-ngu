# Use an official Python runtime as a parent image for ARM architecture
FROM python:3.12.4-buster

# Set the working directory in the container
WORKDIR /pythonProject

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Replace 8000 with the port your app listens on (if applicable)
EXPOSE 8000

# Run main.py when the container launches
CMD ["python", "main.py"]
