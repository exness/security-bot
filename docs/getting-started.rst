Getting Started
===============

On this page, you will find all the necessary information to dive into the
Security Bot (SecBot) project to

* set up the service and the documentation generator it uses,
* configure and integrate it with your service,
* ensure communication via API, and
* get familiar with the main concepts and limits.

Yet, we provide detailed descriptions and insights on separate pages of this
documentation.

Prerequisites
-------------

Since SecBot is a Python application running in a container on Kubernetes,
make sure that the relevant components and their packages are installed and
available in your local environment.

**Kubernetes-related**:

* `Docker <https://docs.docker.com/get-docker/>`_
* `Kubernetes <https://kubernetes.io/docs/setup/>`_
* `Kubernetes Cluster <https://kubernetes.io/docs/tasks/tools/>`_
* Container registry, for example `Docker Hub <https://docs.docker.com/docker-hub/>`_
* and other Containerization tools, for example `Docker Compose <https://docs.docker.com/compose/install/>`_

**Python-related**:

* `Python <https://docs.python.org/3/using/index.html>`_
* `PIP <https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-pip-setuptools-wheel-with-linux-package-managers>`_
* `Poetry <https://python-poetry.org/docs/#installing-with-the-official-installer>`_

Additionally, we employ

* `Sphinx <https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html#quick-start>`_ as a documentation generator and
* `draw.io <https://app.diagrams.net/>`_ as a tool for creating schemes and diagrams.

Deployment
----------

Follow these general steps to install and build the SecBot

1. Clone the repository:

    a. visit the project's repository to copy the URL under :guilabel:`Clone`
    b. run the ``git clone`` command to create a local copy

    .. code-block:: console
    
        $ git clone path/to/project.git

2. Build and run the SecBot service.

    .. code-block:: console
    
        $ docker-compose up --build

Service Configuration
---------------------

The ``/.env.dev`` file defines the location, keys, and other parameters of the
internal and external units SecBot communicates with: queues, databases,
:ref:`Inputs, Scans, Outputs, and Notifiers <glossary_and_inventory>`.

1. Review this file and make the necessary changes to it based on your environment's peculiarities, such as the variables within ``GITLAB_CONFIGS``.
2. Save the file and rebuild the service.

.. code-block:: console
    
    $ docker-compose up --build

For test and other reasons, you can redefine any parameter in the
``/.env.override`` file for your separate sandbox environment. To do this,

1. Rename the original file of ``/.env.override.example`` accordingly
2. Specify the new values of existing variables there, for example modify ``DEFECTDOJO__TOKEN=defectdojo_token``

.. code-block:: text
    
    # Excerpt from .env.override

    ...
    DEFECTDOJO__TOKEN=my_personal_token
    ...

3. Save the file.
4. Rebuild the service.

.. code-block:: console
    
    $ docker-compose up --build

.. note::

    For more detailed information on this topic, see
    :ref:`Configuration <service_configuration>`.

Workflow Configuration
----------------------

The ``/app/config.yml`` file defines the policies SecBot follows in its work:
which Scans to launch to check input entities of a particular type, which
Outputs to use to aggregate the Scans' results, and so on. You can take the
original version and use it as is or update the file according to your needs.
In the latter case, you will need stop and restart the service.

.. code-block:: console

    $ docker-compose stop
    $ docker-compose up -d

.. note::

    For more detailed information on this topic, see
    :ref:`Configuration <workflow_configuration>`.

Integration
-----------

Since SecBot communicates with different units via their respective APIs and
triggers in response to specific input events, you are expected to

* :ref:`obtain authorization with these units <authorization>` (Inputs, Outputs, and Notifiers) and 
* :ref:`specify triggers <input_entity_sources>` on your development and distribution platform (Input), such as system hooks (or webhooks) for GitLab.