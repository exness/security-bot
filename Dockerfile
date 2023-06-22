FROM python:3.9-slim

ARG USER_NAME="exness"
ARG USER_HOME="/${USER_NAME}"
ARG APP_HOME="/opt"

COPY poetry.lock pyproject.toml /

### Add required binaries ###
RUN apt-get update && \
    apt-get install -y git curl && \
    apt-get clean && \
    rm -rf /var/cache/*

RUN apt-get update && \
    apt-get install -qy --no-install-recommends build-essential make && \
    pip install --no-cache-dir --upgrade pip poetry>=1.0.0 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-dev && \
    apt-get remove -qy --purge build-essential && \
    apt-get autoremove --purge -qy && \
    apt-get clean && \
    rm -rf /var/cache/* /poetry.lock /pyproject.toml

### Add worker tools ###

# Install gitleaks
COPY --from=zricethezav/gitleaks:v8.17.0 /usr/bin/gitleaks /usr/local/bin/gitleaks

### Create service user ###
RUN groupadd -g 10001 ${USER_NAME} && useradd -g 10001 -u 10001 -s "/usr/sbin/nologin" -md ${USER_HOME} ${USER_NAME}

### Add application source code ###
COPY docker-entrypoint.sh /usr/local/bin
COPY --chown=10001:10001 app/ ${APP_HOME}/app

ENV PYTHONPATH="${APP_HOME}"

USER ${USER_NAME}
EXPOSE 5000 5001
WORKDIR ${APP_HOME}
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["help"]
