#
# Bases de Dados 2021/2022
# Trabalho Prático
#
# Authors:
#   Nuno Antunes <nmsa@dei.uc.pt>
#   BD 2022 Team - https://dei.uc.pt/lei/
#   University of Coimbra

FROM python:3.9-alpine

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install flask

RUN pip install psycopg2-binary

#?? talvez seja no postman

RUN pip install pyjwt 


#copy . /app

#volume ["/app"]

WORKDIR /app

# RUN mkdir -p logs

EXPOSE 5000

CMD ["python", "project-api.py"]
