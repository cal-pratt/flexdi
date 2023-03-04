What is DI?
===========

Dependency Injection (DI), an implementation of Inversion of Control (IoC), is a 
design pattern in which objects or functions recieve objects they depend on rather 
than constructing these objects themselves.

The main goal of dependency injection is to allow components in your applications
to be loosely coupled to their dependencies. Your component knows how to work with 
its dependencies but does not need to be responsible for constructing them. 

A basic application
-------------------

Consider the following example of a SQLAlchemy application with no dependency injection
which lists all of the tables present in a sqlite database.

.. literalinclude:: ../../examples/why_di.py
   :start-after: [non-injected:start]
   :end-before: [non-injected:end]

In this example, the engine and session objects are constructed directly in the ``main``
function. 

Injecting dependencies
----------------------

If we want to re-use this function for other databases, how could we change what
database instance is selected?

To make our application more flexible, we could move the logic of creating the 
database connection outside of the responsiblilites of the ``main`` function.
We will *inject* the dependency into our function.

.. literalinclude:: ../../examples/why_di.py
   :start-after: [injected-boilerplate:start]
   :end-before: [injected-boilerplate:end]

The main function is now more generic and can be reused for different connection
objects. It no longer carries the concerns of how its dependencies are created.

Reusing dependencies
--------------------

What would we do if we wanted to reuse the logic of creating our dependencies in 
other usecases?

The creation of the engine can be moved to a helper function, and
the creation of the session can be moved to a helper function which is injected 
with the engine as a dependency.

.. literalinclude:: ../../examples/why_di.py
   :start-after: [injected-nicer:start]
   :end-before: [injected-nicer:end]

What's left?
------------

Each component of our script is now much more narrow focused, making them easier
compose into new use-cases. Looking at the application it becomes quite obvious 
how dependencies should be connected:

.. literalinclude:: ../../examples/why_di.py
   :start-after: [injected-interfaces:start]
   :end-before: [injected-interfaces:end]

However, developers are still left with the chore of manually connecting all of 
the components together in the correct order.

.. literalinclude:: ../../examples/why_di.py
   :start-after: [injected-connections:start]
   :end-before: [injected-connections:end]

For applications with dozens to hundreds of components, this can be a painstaking task. 

This is where a dependency injection frameworks like ``flexdi`` become useful.
