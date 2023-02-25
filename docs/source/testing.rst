Testing
-------

Mocking out components during tests in ``flexdi`` application is quite easy.
The ``FlexGraph`` allows users to override pre-defined dependencies with mock
implementations in a way that can be isolated per test case.

Here's how can combine the fixture resolution of ``pytest`` with ``flexdi``

.. include:: ../../examples/test_sqla_sync.py
   :code: python
