Alternatives
------------

Although there are many, many other dependency injection libraries, I found that
I was still left looking for more lightweight/minimal solutions to this problem. 
My thoughts on some of the popular alternatives I have used in the past:

- | `dependency-injector <https://github.com/ets-labs/python-dependency-injector>`_
  | This library is probably the most mature out of all the alternatives.
    Its main driving principal is that "Explicit is better than
    implicit", in that you need to specify explicitly how to assemble/
    inject the dependencies. ``flexdi`` is still explicit in the sense
    that dependencies are directly referenced from their type
    annotations, and by leveraging them we can avoid a lot of the more
    verbose setup required in ``DeclarativeContainer`` structures.

- | `fastapi <https://github.com/tiangolo/fastapi>`_
  | This web framework provides an excellent way to perform dependency injection,
    but it does not provide a way to perform dependency injection outside
    the context of web request. When configuring the injection, you must
    also provide default values to arguments, which ties application code
    to the web framework, making it more difficult to re-use code in
    other contexts. Additionally, it does not provide rich support for
    lifetime/singleton scoped dependencies, making the setup of some
    dependencies increasingly awkward.

- | `pinject <https://github.com/google/pinject>`_
  | This library allows you to perform DI with minimal setup, but its major
    downfall is that it relies on the names of arguments to perform injection.
    If the name of the argument does not match the name of the class, then
    you are forced to bind it explicitly. If there are multiple objects
    that specify a dependency of a particular type, but use different
    names, then you need to bind them all individually as well. And
    sadly, this project has now been archived and is read-only.
