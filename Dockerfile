FROM python:3.7.3
RUN mkdir src/
ADD . /src/
WORKDIR /src/
RUN pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
RUN apt-get  update && install -y --no-install-recommends\
zip\
unzip\
&& rm -rf /var/lib/apt/lists/*