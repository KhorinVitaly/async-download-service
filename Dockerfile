FROM python:3.7.3
RUN mkdir src/
COPY ./requirements.txt src/
WORKDIR /src/
RUN pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
RUN apt-get install -y --no-install-recommends zip unzip