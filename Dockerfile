FROM maven:3.6.0-jdk-8
WORKDIR /app
ADD *.py /app/
ADD *.jar /app/
ADD *.txt /app/
RUN apt update
RUN apt -y install python2.7 python-pip
ADD requirements-pip2.txt .
RUN pip install -r requirements-pip2.txt
ENTRYPOINT ["python", "/app/run-main.py"]