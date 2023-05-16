FROM python:3.10-slim-bullseye

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
RUN python -m spacy download it_core_news_sm

RUN apt update && apt install curl -y

COPY ./app /code/app
COPY ./scripts /code/scripts

RUN chmod +x ./scripts/start.sh

# disables lag in stdout/stderr output
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

CMD ["./scripts/start.sh"]