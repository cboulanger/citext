FROM ubuntu:bionic

# Set the locale
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8

WORKDIR /app
ADD *.py /app/
ADD *.jar /app/
ADD *.txt /app/
RUN apt-get -y install openjdk-8-jdk maven &&\
    apt-get -y install python3.6 python3-pip && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install ruby ruby-dev gem # this installs ruby 2.5.1
ADD requirements.txt .
# python 3.6 because jenkspy is used
RUN  python3.6 -m pip install --upgrade pip && \
     python3.6 -m pip install -r requirements.txt && \
     gem install anystyle
ENTRYPOINT ["python3.6", "/app/run-main.py"]
