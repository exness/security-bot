![security-bot](static/security-bot-logo.png)

Security Bot - Security checks orchestration tool
=======

[![python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390)
[![code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![code style: flake8](https://img.shields.io/badge/code%20style-flake8-blue.svg)](https://github.com/PyCQA/flake8)

The [Security Bot](docs/index.rst) (SecBot) service introduces an additional collection of checks to the SDLC to identify security issues in corporate assets

Reach out to our [Discord server](https://discordapp.com/invite/MqHBT6mg) to communicate with the team more effectively

[![Discord Server](https://discordapp.com/api/guilds/1113355944101957703/widget.png?style=banner3)](https://discordapp.com/invite/MqHBT6mg)

**Technologies: [FastAPI](https://fastapi.tiangolo.com/), [Celery](https://docs.celeryq.dev/en/stable/) + Redis, [SQLAlchemy](https://www.sqlalchemy.org/) + Postgres, Pytest, and others**

## Installation and Tests

#### For sample k8s manifests please refer to [/k8s](/k8s) directory

Deployment:

    git clone path/to/project.git
    docker-compose up --build

Service configuration:

    .env.dev (Default values)
    .env.override (Customized values)

Workflow configuration:

    app/config.yml

## Usage and Support

Documentation:

* [Project documentation (rtd)](https://security-bot.readthedocs.io/en/latest/)
* [Project documentation (local)](docs/index.rst)
