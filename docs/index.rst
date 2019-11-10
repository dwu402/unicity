.. unicity documentation master file, created by
   sphinx-quickstart on Sun Sep  1 19:24:41 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

What is unicity?
----------------

I wrote this library to test the code in the hundreds of Python files submitted by my programming class. It also can be used to spot code submissions that are suspiciously similar.

To get started, first install unicity using ``pip``.

``pip install unicity``

Then download the examples from `https://github.com/ddempsey/unicity 
<https://github.com/ddempsey/unicity>`_. These will show you how to load a project, run a simple test, perform comparisons, and a few other tricks. Or if you prefer a tutorial, see `here <https://sites.google.com/view/dempsey-research-group/unicity>`_.

Some disclaimers:

- I have discovered that students learning to code are very innovative in the ways in which they will break your work flow. Therefore, I have built in catches for **directory changes** and **infinite loops**. But there will be other things I have not anticipated. You may catch and handle these in your test function, but I'd also like to hear if you think something should be added to make the testing more robust.

- The similarity checking should be treated as a screening tool to highlight *potential* instances of copying. It does not (it cannot) assert that copying has actually occurred, and the best way to do that is by interview.

Python classes
--------------

Each submitter is called a **client**. Each client submits a **portfolio** of Python code. The set of all portfolios is called a **project**. The set of all clients is called a **cohort**.

A project is a collection of Python files submitted by several different clients. They should be contained in a zip archive or folder. Each file should follow a particular naming convention 

``{clientname}_*{expected_file}*.{ext}``

where ``{expected_file.ext}`` is passed as an argument to the ``Project`` constructor.

Passing a path to a ``cohort`` file will give the ``Project`` additional data to tag each portfolio and report missing files.

Test parts of the submission using the ``test`` method. This will require you to define a test function, that in turn calls functions or classes from a client's portfolio.

Check similarity metrics across the entire project with the ``compare`` method. You can compare particular methods, exclude similarity deriving from a common template, and compare with past projects.

Projects
~~~~~~~~

.. autoclass:: unicity.Project
	:members:
	
Clients
~~~~~~~

.. autoclass:: unicity.Client
	:members:
	
Comparisons
~~~~~~~~~~~
	
.. autoclass:: unicity.Comparison
	:members:

PythonFiles
~~~~~~~~~~~
	
.. autoclass:: unicity.PythonFile
	:members:

FunctionInfo and ClassInfo
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: unicity.FunctionInfo
	:members:

.. autoclass:: unicity.ClassInfo
	:members:


Indices and tables
==================
	
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
