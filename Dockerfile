# Use the official Python image
FROM python:3.11.6

# Copy the current directory contents into the container at .
COPY . .

# Set the working directory to /
WORKDIR /

# Install requirements.txt 
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Start the FastAPI app on port 7860, the default port expected by Spaces
CMD ["bash", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000"]