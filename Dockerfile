FROM python:3.11.4-bullseye 
WORKDIR /app
RUN apt-get update -y

ADD . .
RUN pip install -r ./requirements.txt
CMD ["python", "main.py"]