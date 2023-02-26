Testing
-------

To mock dependencies in a ``flexdi`` application, the ``FlexGraph`` provides an
override feature. Users can override dependency bindings with mocks in a way that
is isolated per test case and is reverted when the test case completes.

The following examples uses ``pytest`` fixtures to initialize the graph override
and bind mock implementations to the ``FlexGraph``

.. include:: ../../examples/test_sqla_sync.py
   :code: python
