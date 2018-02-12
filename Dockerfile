FROM python:3.5
ADD ./bitcoin-fee-to-latency
WORKDIR ./bitcoin-fee-to-latency
RUN pip install --no-cache-dir -r requirements.txt

CMD main.py