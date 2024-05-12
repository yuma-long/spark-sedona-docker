FROM python:3.10-slim

# Install Java17.
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         openjdk-17-jdk-headless \
         curl \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"

# Set working directory and copy requirements.txt (and other materials if any)
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip \
  && pip install -r requirements.txt

# Install JDBC driver for Postgres.
RUN cd /opt && \
    mkdir -p java/jdbc && \
    cd java/jdbc && \
    curl -LO https://jdbc.postgresql.org/download/postgresql-42.7.3.jar && \
    cd /app

# Set environment variables
ENV CLASSPATH="/opt/java/jdbc/postgresql-42.7.3.jar"
ENV SPARK_HOME="/usr/local/lib/python3.10/site-packages/pyspark"
ENV PATH="${PATH}:${SPARK_HOME}/bin:${JAVA_HOME}/bin"
ENV PYTHONUNBUFFERED True
ENV PYTHONPATH="/app:${SPARK_HOME}/python"

# Ports
EXPOSE 8080

# Execute src/main.py
CMD ["python", "src/main.py"]