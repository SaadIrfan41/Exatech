# Start my Docker image from an existing image that already has Python 3.12 installed.
# We use the "slim" version because it's smaller than the default one.
FROM python:3.12-slim

# creates a directory named app inside the container and sets it as the working directory for subsequent commands (like CMD).
WORKDIR /app

# Copy the Python code from my host (where Dockerfile is) to the /app directory inside the container
# COPY <source> <destination>

COPY app.py ./

# Or we can also do 
# COPY . /app 
# but it will copy all the files from the current directory to the /app directory inside the container
# In this case, '.' means the current directory (where the Dockerfile is located)
# And '/app' is the destination directory inside the container


# This tells Docker: "When someone runs this container, execute the command 'python app.py'"
# CMD is like the default command that runs when the container starts.
# It's the same as running 'python app.py' in your terminal.
CMD [ "python","app.py" ]