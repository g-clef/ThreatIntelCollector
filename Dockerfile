FROM python:3
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ADD ti-collector.conf .
ADD ti_collector.py .
ADD requirements.txt .
RUN pip3 install -r requirements.txt

# Create non-root user
RUN groupadd -g 1000 ticollector && \
    useradd -u 1000 -g ticollector -s /bin/bash ticollector && \
    chown -R ticollector:ticollector /app

# Switch to non-root user
USER ticollector

CMD ["python", "./ti_collector.py"]