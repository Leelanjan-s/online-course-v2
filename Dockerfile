# Use Python 3.10
FROM python:3.10

# Set the working directory
WORKDIR /code

# Copy requirements and install them
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy all your code files
COPY . /code

# Create a folder for the database so it can write to it
RUN mkdir -p /code/data
RUN chmod 777 /code/data

# Start the server on port 7860 (Required for Hugging Face)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
