.. _glossary_and_inventory:

Glossary and Inventory
======================

On this page, you will find the

* brief explanations of the units SecBot's architecture is based on,
* lists of those supported and used in configuration, and
* descriptions of other related concepts.

.. glossary::

    Input
        Input is a code repository, storage, or development or distribution
        platform, such as GitLab or Docker Registry, changes to which need
        extended security-related validation.

        +------------+----------------------------------------------+
        | Input      | Source                                       |
        +============+==============================================+
        | ``gitlab`` | `GitLab Docs <https://docs.gitlab.com/ee/>`_ |
        +------------+----------------------------------------------+

    Input entity
        Input entity (or input event) is a substantial amount of data
        (payload) to be validated. This data can be filtered out based on some
        configuration rules so that only part of it is actually checked. You
        can specify one or more of the event types we support (see the
        following table) and any other keys (JSON paths) of your choice.

        +-------------------+-----------------------------------------------------------------------------------------------------------------------------------------+
        | Event type        | Source                                                                                                                                  |
        +===================+=========================================================================================================================================+
        | ``push``          | `Webhook events: push events <https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#push-events>`_                   |
        +-------------------+-----------------------------------------------------------------------------------------------------------------------------------------+
        | ``tag_push``      | `Webhook events: tag events <https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#tag-events>`_                     |
        +-------------------+-----------------------------------------------------------------------------------------------------------------------------------------+
        | ``merge_request`` | `Webhook events: merge request events <https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#merge-request-events>`_ |
        +-------------------+-----------------------------------------------------------------------------------------------------------------------------------------+

        .. code-block:: text
    
            # Excerpt from /app/config.yml

            ...
            jobs:
              - name: Common merge request event
                rules:
                  gitlab:                           # reserved name (Input)
                    event_type: "merge_request"     # one of the filtering parameters (Event type)
            ...

    Scan
        Scan is an external code analysis tool for applying the DevOps and
        security best practices to development and integration flows. It, for
        example, can detect hardcoded secrets (passwords, API keys, or tokens
        in Git repositories) or evaluate how certain changes might affect the
        overall quality or performance of your application. The result of its
        work is raw defect data to be passed to Outputs.

        +--------------+--------------------------------------------------------------+
        | Scan         | Source                                                       |
        +==============+==============================================================+
        | ``gitleaks`` | `Gitleaks on GitHub <https://github.com/gitleaks/gitleaks>`_ |
        +--------------+--------------------------------------------------------------+
    
    Output
        Output is an external defect management system specially integrated
        with SecBot to aggregate the check results from different Scans, merge
        the duplicates, and do other relevant things to prepare a normalized
        readable report for Notifiers. A piece of this report (problem,
        vulnerability, or any other security issue) is called "finding."

        +----------------+---------------------------------------------------------+
        | Output         | Source                                                  |
        +================+=========================================================+
        | ``defectdojo`` | `DefectDojo on GitHub <https://github.com/DefectDojo>`_ |
        +----------------+---------------------------------------------------------+
    
    Findings
        For findings, see "Output."
    
    Notifier
        Notifier (referred to as "notification" in the `/app/config.py` file)
        is an instant messaging program integrated with SecBot to inform
        interested parties of detected security issues (findings).

        +-----------+---------------------------------------+
        | Notifier  | Source                                |
        +===========+=======================================+
        | ``slack`` | `Slack Website <https://slack.com/>`_ |
        +-----------+---------------------------------------+

    Job
        Job is three sets of tasks, at least one for a Scan, one for an
        Output, and one for a Notifier, to be executed sequentially to process
        a particular input entity type and yield the relevant results (findings).