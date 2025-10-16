# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the entire project into the container
COPY . /app

# Make the scripts executable
RUN chmod +x /app/scripts/build.sh /app/scripts/start.sh

# Run the build script to install dependencies and set up the environment
# This is run during the image build process
RUN /app/scripts/build.sh

# Expose the port the app runs on
# The $PORT environment variable will be set by Render, default to 8000
EXPOSE 8000

# Define the command to run the application
# This will be executed when the container starts
CMD ["/app/scripts/start.sh"]