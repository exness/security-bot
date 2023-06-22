Configuration
=============

The content of this page is focused on the peculiarities and details of the
service and workflow configuration files to let you make more informed
decisions when customizing the Security Bot (SecBot) service for your needs.

.. _service_configuration:

Service Configuration
---------------------

SecBot's configuration implies setting up all the

* internal (queues and databases) and
* external (Inputs, Scans, Outputs, and Notifiers) units

this service collaborates with and specifying other relevant parameters
(metrics) as well.

Therefore, you need to review and update the respective ``/.env.dev`` file in
advance to reflect your environment's peculiarities.

.. code-block:: text

    # Excerpt from .env.dev

    ...
    CELERY_BROKER_URL=redis://redis:6379/0
    CELERY_RESULT_BACKEND=redis://redis:6379/0

    SECBOT_POSTGRES_DSN=postgresql+asyncpg://secbot:foobar@db:5432/secbot

    GITLAB_CONFIGS=[
        {
            "host":"https://git.env.local/",        # GitLab's host (instance)
            "webhook_secret_token":"SecretStr",     # secret token used when a webhook is being set up
            "auth_token":"SecretStr",               # token given to the user who will communicate with the API to get check results
            "prefix":"GIT_LOCAL"                    # prefix used when a security_check_id is being generated
        }
    ]

    DEFECTDOJO__URL=https://defectdojo.env.local    # DefectDojo's host
    DEFECTDOJO__TOKEN=defectdojo_token              # token given upon user registration to communicate with the DefectDojo's API
    DEFECTDOJO__USER=defectdojo_username            # registered user's name
    DEFECTDOJO__USER_ID=10                          # registered user's ID

    SLACK_TOKEN=token_here                          # token given to the user that is allowed to read Slack's channels
    ...

After that, save the file and rebuild the service.

.. code-block:: console
    
    $ docker-compose up --build

Additionally, according to the ``/.gitignore`` file, any parameter specified
in ``/env.dev`` can be redefined in ``/.env.override`` for testing and other
purposes.

.. code-block:: text
    
    # Excerpt from .gitignore

    ...
    # Personal override env
    .env.override
    ...

To do this,

1. Rename the original file of ``/.env.override.example`` accordingly
2. Specify the new values of existing variables there, for example modify ``DEFECTDOJO__TOKEN=defectdojo_token``

.. code-block:: text
    
    # Excerpt from .env.override

    ...
    DEFECTDOJO__TOKEN=my_personal_token
    ...

3. Save the file.
4. Rebuild the service.

.. _workflow_configuration:

Workflow Configuration
----------------------

The workflow configuration is a set of policies according to which SecBot
reacts to incoming events, processes the data, and yields the results. This
configuration is based on the ``app/config.yml`` file that contains two
sections: *components* and *jobs*.

The first section introduces the hired external units (Scans, Outputs, and
Notifiers) which SecBot collaborates with. It might include a unit’s name
(handler name) and its settings: format of data it returns, URLs, keys, etc.

The following excerpt shows an example of three units belonging to different
types. (The environment variable values refer to the ``.env.dev`` file.)

.. code-block:: yaml
    
    # Excerpt from app/config.yml

    ...
    components:
        # Scan Gitleaks
        gitleaks:
            handler_name: "gitleaks"
            config:
                format: "json"                      # data format in a response
        # Output DefectDojo
        defectdojo:
            handler_name: "defectdojo"
            env:
                url: "DEFECTDOJO__URL"              # host
                secret_key: "DEFECTDOJO__TOKEN"     # token given upon user registration to communicate with the API
                user: "DEFECTDOJO__USER"            # registered user's name
                lead_id: "DEFECTDOJO__USER_ID"      # registered user's ID
        # Notifier Slack
        slack:
            handler_name: "slack"
            config:
                render_limit: 10                    # maximum number of lines (findings) in a notification
                channel:                            # channels to report findings
                    - test-sec-security-bot
                    - my-personal-channel
            env:
                token: "SLACK_TOKEN"                # token given to the user that is allowed to read the channels
    ...

.. note::

    For now, these are the only components SecBot collaborates with. However,
    it must be sufficient for the first version of the product to let you
    assess its work.

The second section, "jobs", defines the policies SecBot follows in its work to
yield the results. When a specific event matching the *rules* of a
policy comes up, a processing plan (job) is created. It contains the necessary
number of tasks to be sequentially executed by the relevant external units
(components).

The following excerpts from the ``app/config.yml`` file show an example of one job
to explain the idea.

.. code-block:: yaml

    # Excerpt from app/config.yml

    ...
    jobs:
        # human-readable job name to be used as a reference in logs
        - name: Common merge request event
            
        # two-level identifier of an input entity 
        rules:
            gitlab:                                         # first level
                event_type: "merge_request"                 # second level
                project.path_with_namespace: /gitlab-test/  # second level
                
, where

* **first level** is a development or distribution platform (Input) or any custom workflow name.
* **second level** is :term:`Input entity` (input event) types and keys (JSON path strings) to apply checks and filtration within the input events. For available keys, refer to the objects from a payload (request body). For example, ``project.path_with_parameters`` from ``POST [host]/v1/gitlab/webhook`` enables the filtering of input events originating from specific repositories.

Also, note that the arguments at the second level are joined with logical AND
unless they are matching and thus mutually exclusive. That is, if, for
example, ``event_type: "tag_push"`` and ``event_type: "merge_request"`` are
specified in the same job, the last one will be taken.

.. code-block:: yaml

    # Excerpt from app/config.yml (continuation)

        # handlers to find leaks, vulnerabilities, and other security-related issues
        scans:
            - gitleaks
            
        # handlers to aggregate and normalize the Scans' results
        outputs:
            - defectdojo

        # handlers to report the Outputs' results
        notifications:
            - slack
    ...

.. note::

    For now, only one job is allowed to cover a particular event. If your
    configuration implies that two or more jobs can be created to serve the
    same event, it will result in an error.

Information from the ``app/config.yml`` file is read once as soon as SecBot
starts. Therefore, if you make any changes to it, you need to stop and restart
the service to apply them.

.. code-block:: console

    $ docker-compose stop
    $ docker-compose up -d