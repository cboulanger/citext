FROM ubuntu:bionic
WORKDIR /app
ADD *.py /app/
ADD *.jar /app/
ADD *.txt /app/
RUN apt-get update -y && \
    apt-get install openjdk-8-jdk -y && \
    apt-get install maven -y && \
    apt-get -y install python3.6 && \
    apt-get -y install python3-pip
ADD requirements.txt .
# 3.6 because jenkspy is used
RUN  python3.6 -m pip install --upgrade pip && \
     python3.6 -m pip install -r requirements.txt
ENTRYPOINT ["python3.6", "/app/run-main.py"]