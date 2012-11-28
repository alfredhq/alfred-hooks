Alfred Hooks
============

.. image:: https://secure.travis-ci.org/alfredhq/alfred-hooks.png?branch=develop
    :target: https://travis-ci.org/alfredhq/alfred-hooks

This app manages github service hooks for alfred.

Tasks must be sent as dicts:

.. code:: python

    {
        'user_id': 5123,
        'repo_id': 43213
    }

You can run it using this command::

  $ alfred-hooks config.yml

Config example:

.. code:: yaml

  num_workers: 2
  listener_url: "http://listener.alfredhq.org"
  hooks: "tcp://127.0.0.1:34125"
  database_uri: "postgresql://localhost/alfred"

