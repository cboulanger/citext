FROM maven:3.6.0-jdk-8
RUN ls -al
RUN mkdir /app
WORKDIR /app
# ADD . .
ADD *.py /app/
ADD *.jar /app/
ADD *.txt /app/
# refreshing the repositories
RUN apt update
# you can skip the following line if you not  want to update all your software
# RUN apt upgrade
# installing python 2.7 and pip for it
RUN apt -y install python2.7 python-pip
ADD requirements-pip2.txt .
RUN pip install -r requirements-pip2.txt

ENTRYPOINT ["python", "/app/run-main.py"]
