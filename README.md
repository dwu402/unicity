# unicity

I wrote this library to test the code in the hundreds of Python files submitted by my programming class. It also can be used to spot code submissions that are suspiciously similar.

To get started, first install unicity using ``pip``.

```bash
pip install unicity
```

Then download the and run the scripts in the examples folder, particularly loading_projects.py, batch_testing.py and similarity_check.py.

Some disclaimers:

- I have discovered that students learning to code are very innovative in the ways in which they will break your work flow. Therefore, I have built in catches for **directory changes** and **infinite loops**. But there will be other things I have not anticipated. You may catch and handle these in your test function, but I'd also like to hear if you think something should be added to make the testing more robust.

- The similarity checking should be treated as a screening tool to highlight *potential* instances of copying. It does not (it cannot) assert that copying has actually occurred, and the best way to do that is by interview.
