otpl-service-check
==================
Basic Nagios/Sensu checks for OpenTable Discovery services.

Distribution
------------
`<https://pypi.python.org/pypi/otpl-service-check>`_

Arguments
---------
Run with ``-h`` or ``--help`` to see command-line argument
documentation.

Interface
---------
If there is an error parsing command-line arguments, we return with exit
code 3 (``UNKNOWN``) and print the invocation error.

If there is an error reaching Discovery and parsing the announcements
for your service, we return with exit code 3 (``UNKNOWN``).

We log critical and warning statuses related to announcement, and return
with exit codes 2 (``CRITICAL``) and 1 (``WARNING``)
respectively.

If your endpoint returns with status code ``2xx``, this is
considered a success.  If it returns with ``4xx``, this is
considered a warning (exit code 1).  ``5xx`` is considered critical
(exit code 2).  In the latter two cases, in addition to logging the
service status, we log a small number of characters from each endpoint
response.

*All* critical statuses, warnings, and successes are logged, and the
exit status of the whole process is the worst of the set.

Endpoint Response Codes
-----------------------
* ``2xx``: ``0``, ``OK``
* ``4xx``: ``1``, ``WARNING``
* ``5xx``: ``2``, ``CRITICAL``

This is *a bit of an abuse* of HTTP response codes, but our policy is
that this is the simplest and most flexible way to get rich status
responses from health check endpoints.

Notes
-----
Nagios and Sensu plugin API documentation:

* `<https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/3/en/pluginapi.html>`_
* `<https://sensuapp.org/docs/latest/reference/plugins>`_
