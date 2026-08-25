# ok start with a lightweight python image
FROM python:3.11-slim

# work directory inside docker
WORKDIR /app

# copy requirements into app | we do this first bcoz docker build uses cache ..so every time you make a file change, you wont have to download packages
COPY requirements.txt .
# install dependencies by running the cmd for pip install
RUN pip install --no-cache-dir -r requirements.txt  

# copy code files into image
COPY app ./app

# fastapi listens on port 
EXPOSE 8000

# different than RUN coz it is used to run a container
# There can only be one CMD instruction in a Dockerfile. If you list more than one CMD, only the last one takes effect.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]