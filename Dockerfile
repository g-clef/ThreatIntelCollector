FROM python:3
RUN apt-get install -y git
WORKDIR /app
ADD ti-collector.conf .
ADD ti-collector.py .
ADD requirements.txt .
RUN pip3 install -r requirements.txt
CMD["python", "./ti-collector.py"]