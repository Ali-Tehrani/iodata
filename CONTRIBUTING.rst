We'd love you to contribute. Here are some practical hints to help out.


General recommendations
-----------------------

- Please, be careful with tools like autopep8, black or yapf. They may result in
  a massive number of changes, making pull requests harder to review. Also, when
  using them, use a maximum line length of 100. To avoid confusion, only clean
  up the code you are working on. A safer option is to use
  ``cardboardlint -F -r master``. This will only clean code where you have
  already made changes.

- Do not add module-level ``pylint: disable=...`` lines, except for the
  ``no-member`` warning in the unit test modules. When adding pylint exception,
  place them as locally as possible and make sure they are justified.

- Use `type hinting`_ to document the types of function (and method) arguments
  and return values. This is not yet consistently done throughout IOData at the
  moment, but it would be helpful to do so in future pull requests. Avoid using
  strings to postpone the evaluation of the type. (See `PEP 0563`_ for more
  details on postponed type annotation.)

- In unit testing, use ``np.testing.assert_allclose`` and
  ``np.testing.assert_equal`` for comparing floating-point and integer numpy
  arrays respectively. ``np.testing.assert_allclose`` can also be used for
  comparing floating point scalars. In all other cases (not involving floating
  point numbers), the simple ``assert a == b`` works equally well and is more
  readable.


Adding new file formats
-----------------------

Each file format is implemented in a module of the package ``iodata.formats``.
These modules all follow the same API. Please consult existing formats for some
guidance, e.g. the :py:mod:`iodata.formats.xyz` is a simple but complete
example. From the following list, ``PATTERNS`` and one of the functions must
be implemented:

* ``PATTERNS = [ ... ]``: a list of glob patterns used to recognize file formats
  from the file names. This is used to select the correct module from
  ``iodata.formats`` in functions in ``iodata.api``.
* ``load_one``: load a single IOData object.
* ``dump_one``: dump a single IOData object.
* ``load_many``: load multiple IOData objects (iterator) from a single file.
* ``dump_many``: dump multiple IOData objects (iterator) to a single file.


``load_one`` function: reading a single IOData object from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to read from a new file format, the module must contain a ``load_one``
function with the following signature:

.. code-block :: python

    @document_load_one("format", ['list', 'of', 'guaranteed', 'attributes'],
                       ['list', 'of', 'attributes', 'which', 'may', 'be', 'read'],
                       notes)
    def load_one(lit: LineIterator) -> dict:
        """Do not edit this docstring. It will be overwritten."""
        # Actual code to read the file


The ``LineIterator`` instance provides a convenient interface for reading files
and can be found in ``iodata.utils``. As a rule of thumb, always use
``next(lit)`` to read a new line from the file. You can use this iterator in
a few ways:

.. code-block:: python

    # When you need to read one line.
    line = next(lit)

    # When sections appear in a file in fixed order, you can use helper functions.
    data1 = _load_helper_section1(lit)
    data2 = _load_helper_section2(lit)

    # When you intend to read everything in a file (not for trajectories).
    for line in lit:
        # do something with line.

    # When you just need to read a section.
    for line in lit:
        # do something with line
        if done_with_section:
            break

    # When you need a fixed numbers of lines, say 10.
    for i in range(10):
        line = next(lit)

    # More complex example, in which you detect several sections and call other
    # functions to parse those sections. The code is not sensitive to the
    # order of the sections.
    while True:
        line = next(lit)
        if end_pattern in line:
            break
        elif line == 'section1':
            data1 = _load_helper_section1(lit)
        elif line == 'section2':
            data2 = _load_helper_section2(lit)

    # Same as above, but reading till end of file. You cannot use a for loop
    # when multiple lines must be read in one iteration.
    while True:
        try:
            line = next(lit)
        except StopIteration:
            break
        if end_pattern in line:
            break
        elif line == 'section1':
            data1 = _load_helper_section1(lit)
        elif line == 'section2':
            data2 = _load_helper_section2(lit)


In some cases, one may have to push back a line because it was read too early.
For example, in the Molden format, this is sometimes unavoidable. When needed
you can *push back* the line for later reading with ``lit.back(line)``.

.. code-block:: python

    # When you just need to read a section
    for line in lit:
        # do something with line
        if done_with_section:
            # only now it becomes clear that you've read one line to far
            lit.back(line)
            break

When you encounter a file-format error while reading the file, call
``lit.error(msg)``, where ``msg`` is a short message describing the problem.
The error appearing on screen will automatically also contain the filename
and line number.


``dump_one`` functions: writing a single IOData object to a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``dump_one`` functions are conceptually simpler: they just receive an open
file object and an ``IOData`` instance as arguments, and should write the data
to the open file.

.. code-block:: python

    @document_dump_one("format", ['guaranteed', 'attributes'], ['optional', 'attribtues'], notes)
    def dump_one(f: TextIO, data: IOData):
        """Do not edit this docstring. It will be overwritten."""
        # code to write data to f.


``load_many`` function: reading multiple IOData objects from a single file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function works essentially in the same way as ``load_one``, but can load
multiple molecules. For example:

.. code-block :: python

    @document_load_many("XYZ", ['atcoords', 'atnums', 'title'])
    def load_many(lit: LineIterator) -> Iterator[dict]:
        """Do not edit this docstring. It will be overwritten."""
        # XYZ Trajectory files are a simple concatenation of individual XYZ files,'
        # making it travial to load many frames.
        while True:
            try:
                yield load_one(lit)
            except StopIteration:
                return


The XYZ trajectory format is simply a concatenation of individual XYZ files,
such that one can use the load_one function to read a single frame. In some
file formats, more complicated approaches are needed. In any case, one must
use the ``yield`` keyword for every frame read from a file.


``dump_many`` function: writing multiple IOData objects to a single file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Also ``dump_many`` is very similar to ``dump_one``, but just takes an iterator
over multiple IOData instances as argument. It is expected to write all of these
to a single open file object. For example:

.. code-block :: python

    @document_dump_many("XYZ", ['atcoords', 'atnums'], ['title'])
    def dump_many(f: TextIO, datas: Iterator[IOData]):
        """Do not edit this docstring. It will be overwritten."""
        # Similar to load_many, this is relatively easy.
        for data in datas:
            dump_one(f, data)

Also here, we take advantage of the simple structure of the XYZ trajectory
format, i.e. the simple concatenation of individual XYZ files. For other
formats, this could become more complicated.


Github work flow
----------------

1. Before diving into technicalities: if you intend to make major changes,
   beyond fixing bugs and small functionality improvements, please open a Github
   issue first, so we can discuss before coding. Please explain what you intend
   to accomplish and why. That often saves a lot of time and trouble in the long
   run.

   Use the issue to plan your changes. Try to solve only one problem at a time,
   instead of fixing several issues and adding different features in a single
   shot. Small changes are easier to handle, also for the reviewer in the last
   step below.

   Mention in the corresponding issue when you are working on it. "Claim" the
   issue to avoid duplicate efforts.

2. Install Roberto, which is the driver for our CI setup. It can also replicate
   the continuous integration on your local machine, which makes it easier to
   prepare a passable pull request. See https://theochem.github.io/roberto/

3. Make a fork of the project, using the Github "fork" feature.

4. Clone the original repository on your local machine and enter the directory

   .. code-block:: bash

    git clone git@github.com:theochem/iodata.git
    cd iodata

5. Add your fork as a second remote to your local repository, for which we will
   use the short name ``mine`` below, but any short name is fine:

   .. code-block:: bash

    git remote add mine git@github.com:<your-github-account>/iodata.git

6. Make a new branch, with a name that hints at the purpose of your
   modification:

   .. code-block:: bash

    git checkout -b new-feature

7. Make changes to the source. Please, make it easy for others to understand
   your code. Also, add tests that verify your code works as intended.
   Rules of thumb:

   - Write transparent code, e.g. self-explaining variable names.
   - Add comments to passages that are not easy to understand at first glance.
   - Write docstrings explaining the API.
   - Add unit tests when feasible.

8. Commit your changes with a meaningful commit message. The first line is a
   short summary, written in the imperative mood. Optionally, this can be
   followed by an empty line and a longer description.

   If you feel the summary line is too short to describe what you did, it
   may be better to split your changes into multiple commits.

9. Run Roberto and fix all problems it reports. Either one of the following
   should work

   .. code-block:: bash

    rob                 # Normal case
    python3 -m roberto  # Only if your PATH is not set correctly

   Style issues, failing tests and packaging issues should all be detected at
   this stage.

10. Push your branch to your forked repository on Github:

    .. code-block:: bash

        git push mine -u new-feature

    A link should be printed on screen, which will take the next step for you.

11. Make a pull request from your branch `new-feature` in your forked repository
    to the `master` branch in the original repository.

12. Wait for the tests on Travis-CI to complete. These should pass. Also
    coverage analysis will be shown, but this is merely indicative. Normally,
    someone should review your pull request in a few days. Ideally, the review
    results in minor corrections at worst. We'll do our best to avoid larger
    problems in step 1.

.. _type hinting: https://docs.python.org/3/library/typing.html
.. _PEP 0563: https://www.python.org/dev/peps/pep-0563/
