===============
Version History
===============

v7.0.0
------

* Update love producer to make it compatible with salobj-kafka.
  This changes are not backward compatible.
* Remove build directory.

v6.8.0
------

* Make scripts schemas load on startup optional for the love_producer_script_queue. `<https://github.com/lsst-ts/LOVE-producer/pull/153>`_
* Make subscriptions to initial state periodically. `<https://github.com/lsst-ts/LOVE-producer/pull/152>`_

v6.7.0
------

* Log exception to identify issues when the producer process ends suddenly. `<https://github.com/lsst-ts/LOVE-producer/pull/151>`_
* Limit size of stored finished scripts list. `<https://github.com/lsst-ts/LOVE-producer/pull/150>`_

v6.6.1
------

* Hook up to the ts_jenkins_shared_library `<https://github.com/lsst-ts/LOVE-producer/pull/149>`_

v6.6.0
------

* Remove authlist references `<https://github.com/lsst-ts/LOVE-producer/pull/148>`_
* Refactor ScriptQueueState payload into several `<https://github.com/lsst-ts/LOVE-producer/pull/147>`_

v6.5.4
------

* Hotfix for Jenkinsfile `<https://github.com/lsst-ts/LOVE-producer/pull/146>`_
* Minor adjustments for documentation pipeline `<https://github.com/lsst-ts/LOVE-producer/pull/144>`_
* Add ts_pre_commit_conf `<https://github.com/lsst-ts/LOVE-producer/pull/145>`_

v6.5.3
-------

* Improve copyright file `<https://github.com/lsst-ts/LOVE-producer/pull/143>`_
* LOVE License `<https://github.com/lsst-ts/LOVE-producer/pull/142>`_

v6.5.2
-------

* Adjust jenkinsfile pipeline to properly create apidoc `<https://github.com/lsst-ts/LOVE-producer/pull/141>`_
* Refactor documentation `<https://github.com/lsst-ts/LOVE-producer/pull/140>`_

v6.5.1
-------

* Add changelog checker `<https://github.com/lsst-ts/LOVE-producer/pull/139>`_

v6.5.0
-------

* Refactor Watcher alarms handling `<https://github.com/lsst-ts/LOVE-producer/pull/138>`_

v6.4.4
-------

* Update Sphinx dependencies `<https://github.com/lsst-ts/LOVE-producer/pull/137>`_

v6.4.3
-------

* Add repository version history `<https://github.com/lsst-ts/LOVE-producer/pull/136>`_

v6.4.2
------

* tickets/SITCOM-432 `<https://github.com/lsst-ts/LOVE-producer/pull/135>`_

v6.4.1
------

* Fix entrypoints `<https://github.com/lsst-ts/LOVE-producer/pull/134>`_

v6.4.0
------

* Update build to pyproject.toml `<https://github.com/lsst-ts/LOVE-producer/pull/133>`_

v6.3.0
------

* Rename {CSC}ID field to salIndex `<https://github.com/lsst-ts/LOVE-producer/pull/132>`_

v6.2.2
------

* In ScriptQueue producer, skip reply to message if it fails to determine the sample name `<https://github.com/lsst-ts/LOVE-producer/pull/131>`_

v6.2.1
------

* Tickets/dm 34255 `<https://github.com/lsst-ts/LOVE-producer/pull/130>`_
* Adjust permissions on Dockerfile `<https://github.com/lsst-ts/LOVE-producer/pull/129>`_

v6.2.0
------

* Refactor docker files path `<https://github.com/lsst-ts/LOVE-producer/pull/128>`_

v6.0.1
------

* `<https://github.com/lsst-ts/LOVE-producer/pull/127>`_ In ScriptQueue producer:

    * Fix issue when producer is sending log messages for a script when the script finishes executing.
    * Fix handling Script heartbeats monitor.

v6.0.0
------

* Tickets/dm 31183 `<https://github.com/lsst-ts/LOVE-producer/pull/125>`_

v5.1.5
------

* Upgrade dev-cycle to c0021.007 `<https://github.com/lsst-ts/LOVE-producer/pull/124>`_
* Remove editable mode for pip install `<https://github.com/lsst-ts/LOVE-producer/pull/123>`_
* Rollback package installation to runtime `<https://github.com/lsst-ts/LOVE-producer/pull/122>`_

v5.1.3
------

* ScriptQueue initialization is not compliant with the new version of the LOVE-producer `<https://github.com/lsst-ts/LOVE-producer/pull/121>`_

v5.1.2
------

* Refactor to install package at build time `<https://github.com/lsst-ts/LOVE-producer/pull/120>`_

v5.1.1
------

* Tickets/dm 30852 `<https://github.com/lsst-ts/LOVE-producer/pull/119>`_
* Bump websockets from 8.1 to 9.1 `<https://github.com/lsst-ts/LOVE-producer/pull/118>`_
* Bump websockets from 8.1 to 9.1 in /python/love/producer/love_csc `<https://github.com/lsst-ts/LOVE-producer/pull/117>`_
* Remove .egg-info folder `<https://github.com/lsst-ts/LOVE-producer/pull/115>`_

v5.1.0
------

* Refactor LOVE-producer code base so it is better organized as a python package. `<https://github.com/lsst-ts/LOVE-producer/pull/114>`_
* Upgrade dev-cycle to c0020.001 `<https://github.com/lsst-ts/LOVE-producer/pull/113>`_
* Bump eventlet from 0.24.1 to 0.31.0 in /producer `<https://github.com/lsst-ts/LOVE-producer/pull/112>`_

v5.0.0
------

* Release/5.0.0 `<https://github.com/lsst-ts/LOVE-producer/pull/111>`_
* Fix failing tests due to new LOVE-producer `<https://github.com/lsst-ts/LOVE-producer/pull/110>`_
* Reduce heartbeat timeout to solve performance issue `<https://github.com/lsst-ts/LOVE-producer/pull/109>`_
* Update test due to a recent change on the CSC client `<https://github.com/lsst-ts/LOVE-producer/pull/108>`_
* Script logMessages is not compatible with the new Producer version `<https://github.com/lsst-ts/LOVE-producer/pull/107>`_
* Upload producer diagram `<https://github.com/lsst-ts/LOVE-producer/pull/106>`_
* Upgrade develop-env to c0018.001 `<https://github.com/lsst-ts/LOVE-producer/pull/104>`_

v4.0.0
------

* Rollback to dev env version c0017.000 `<https://github.com/lsst-ts/LOVE-producer/pull/103>`_
* Upgrade to lsstts/develop-env:c0018.000 `<https://github.com/lsst-ts/LOVE-producer/pull/102>`_
* Build from tickets branches `<https://github.com/lsst-ts/LOVE-producer/pull/101>`_
* Stop installing ts-idl in the Dockerfile-deploy as that is already … `<https://github.com/lsst-ts/LOVE-producer/pull/100>`_
* Include pre-commit config file `<https://github.com/lsst-ts/LOVE-producer/pull/99>`_
* Add lsstts/develop-env to docker-compose `<https://github.com/lsst-ts/LOVE-producer/pull/98>`_
* Fix ScriptQueue not properly setting up callbacks `<https://github.com/lsst-ts/LOVE-producer/pull/97>`_
* Black formatter fixes `<https://github.com/lsst-ts/LOVE-producer/pull/96>`_
* Sonarqube fixes `<https://github.com/lsst-ts/LOVE-producer/pull/95>`_
* Update jenkinsfile to publish documentation `<https://github.com/lsst-ts/LOVE-producer/pull/94>`_
* Xml version fix `<https://github.com/lsst-ts/LOVE-producer/pull/93>`_
* Build love-producer with deployment image. `<https://github.com/lsst-ts/LOVE-producer/pull/92>`_
* Add dynamic way to set lsstts/develop-env image version `<https://github.com/lsst-ts/LOVE-producer/pull/91>`_
* Script heartbeats fix `<https://github.com/lsst-ts/LOVE-producer/pull/90>`_
* Csc producer fixes `<https://github.com/lsst-ts/LOVE-producer/pull/89>`_
* Get schema fix `<https://github.com/lsst-ts/LOVE-producer/pull/88>`_
* Remotes refactor `<https://github.com/lsst-ts/LOVE-producer/pull/87>`_
