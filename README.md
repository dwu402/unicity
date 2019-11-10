# unicity

I wrote this library to test and debug code from hundreds of Python files submitted by my programming class. It can also be used to find code submissions that are suspiciously similar (Python and MATLAB).

To get started, install unicity using ``pip``.

```bash
pip install unicity
```

Then, download the and run the scripts in the [``example``](https://github.com/ddempsey/unicity/tree/master/example) folder above. Or if you prefer a tutorial, see [here](https://sites.google.com/view/dempsey-research-group/unicity).

Some disclaimers:

- I have discovered that when students are learning to code, they are very innovative in the ways they will find to break your workflow. So far, I have built support to catch and handle **directory changes**, **infinite loops**, and **widespread typos**, but I'm sure there are more surprises out there! You can catch and handle these yourself in the way you define a test function, but I'd also like to hear if you think something should be added to make unicity testing more robust.

- Similarity checking should be treated as a screening tool to highlight *potential* instances of copying. It does not (it cannot) assert that copying has in fact occurred. The best way to do that is by a follow up interview.

More documentation at [readthedocs](https://unicity.readthedocs.io/en/latest/).