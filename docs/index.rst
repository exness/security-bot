.. security-bot documentation master file, created by
   sphinx-quickstart on Thu May 18 11:38:18 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Security Bot's documentation!
========================================

.. toctree::
   :hidden:
   
   Welcome to SecBot <self>
   getting-started
   configuration
   integration
   glossary

The **Security Bot** (SecBot) is an orchestration service designed to
communicate with various external units (see the :ref:`following scheme <general-scheme-image>`)
to detect security-related issues in developers' code. It can be implemented
as an extra pipeline stage to be passed (along with linting, unit-tests, and
build) or used in any other way.

In its work, this service

1. receives from development and distribution platforms ("Inputs") information on changes that a software engineer contributes ("input entity")
2. based on its configuration and the input entity's type, draws up a processing plan ("job"; see an example of it :ref:`later <job-graph-image>`)
3. according to this plan, creates a necessary number of tasks for different units to be successively performed to

    a. scan the input entity with code analysis tools ("Scans")
    b. aggregate the found security issues from Scans, merge duplicates, and do other relevant things with defect management systems ("Outputs")
    c. inform the interested parties of the results by means of instant messaging ("Notifiers")

4. provides the "Input" platforms with the check results (status) on request. (Based on this status—"success" or "fail"—the changes being contributed are allowed or blocked.)

.. _general-scheme-image:

.. image:: /images/general-scheme.drawio.png
   :alt: General scheme

.. note::

   As the scheme suggests, SecBot is split into two instances running in
   separate containers to ensure high availability and distribute the load.
   One instance is responsible for receiving requests to process data, whereas
   the other is dedicated to providing the results of this processing.

.. _job-graph-image:

The following example of a processing plan, presented as a graph, implies that
SecBot's job is configured to use two Scans, three Outputs, and one Notifier.
The overall number of tasks is 11.

.. image:: /images/job-graph.drawio.png
   :width: 350px
   :align: center
   :alt: Job graph