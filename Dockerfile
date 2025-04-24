# Use the official Python image
FROM python:3.11.6

# Copy the current directory contents into the container at .
COPY . .

# Set the working directory to /
WORKDIR /

# Install requirements.txt 
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN mkdir -p /app/creds


ENV STREAMLIT_WATCH_USE_POLLING=true

EXPOSE 7860
# Start the FastAPI app on port 7860, the default port expected by Spaces
CMD ["./start.sh"]