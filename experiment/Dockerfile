FROM python:3.6-slim

RUN apt-get update
RUN apt-get install -y libssl-dev

# Output to docker logs
ENV PYTHONUNBUFFERED=0

#RUN mkdir /experiment
RUN mkdir -p /experiment/data
ADD . /experiment

WORKDIR /experiment
RUN python -m pip install -r requirements.txt

RUN mkdir /root/.bitcoin

CMD python /experiment/live_tracking.py
