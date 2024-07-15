# Use an official Python runtime as a parent image
FROM python:3.12.4-alpine

# Set the working directory in the container
WORKDIR /pythonProject

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/cache/apk/* /root/.cache

# Copy the rest of the application code into the container
COPY . .

# Replace 8000 with the port your app listens on (if applicable)
EXPOSE 8000

# Run main.py when the container launches
CMD ["python", "main.py"]