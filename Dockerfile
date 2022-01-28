FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install vim -y


# copy every content from the local file to the image
COPY . /src
# switch working directory
WORKDIR /src

ENV PYTHONPATH "${PYTHONPATH}:/src"

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt


# configure the container to run in an executed manner
ENTRYPOINT [ "python3" ]

CMD [ "web_application/app.py" ]