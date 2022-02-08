FROM ubuntu:bionic

# Set the locale
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8
#

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