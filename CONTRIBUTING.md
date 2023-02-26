# Want to make a contribution?

Start off by looking throug any open issues regarding the feature you would
like to create, and if there is any ongoing work for that issue.

If there is not an issue already created, feel free to open one and we can
discuss solutions. When a solution is agreed upon, fork this repo and create
a pull request towards the main branch of this repo.

For very small requests or bug fixes, feel free to post a PR directly, and
we can also discuss it there further.

# Installing the local dev environment

This project uses [nox](https://nox.thea.codes/en/stable/) to execute all
tests and CI actions. See the `nox` documentation for steps on how to install.

The `noxfile.py` in this repo has been configured with Python 3.11 as it's
default interpretter version, but you can modify this to a version of your
choosing of Python >= 3.8. Make sure not to commit this change.

To create a virtual environment with all dependencies installed, you can run:

```sh
$ nox -e dev
```

The virtual environment created will be under `.nox/dev` in the project root.

On Widnows you can enter the environment by running `.\\.nox\\dev\\Scripts\\activate`,

On linux and MacOS run `source .nox/dev/bin/activate`

# Developing code

* Make sure to run and create the unit tests:
  * `nox -e tests --python=3.X`
  * or `pytest tests/`
* Make sure the type hints are valid:
  * `nox -e mypy`
  * or `mypy --strict src/ tests/`
* Format the code with black and isort:
  * `nox -e clean`
  * or `black src/ tests/ examples/ && isort src/ tests/ examples/`
* Check that we pass flake8 rules:
  * `nox -e flake8`
  * or `flake8 src/ tests/`
* Check the documetnation:
  * `nox -e docs`
    * This step must be done with `nox`, as there is logic in there to
      recreate the README.rst.
    * Once created you can view them by opening `./docs/build/index.html`

# Pull Requests

Once the code is ready for review, open a pull request with the GitHub
issue linked in the description body. This will need to pass all CI before
being merged. Once merged the owners of the repo will publish the changes
to PyPI for you.
