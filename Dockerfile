FROM python:3.7

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app/

COPY .. /usr/src/app/

RUN apt-get update && apt-get install -y netcat

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

#run entrypoint.sh
ENTRYPOINT ["/usr/src/app/scripts/run_web.sh"]
