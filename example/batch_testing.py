from unicity import Project 

def test_function():
    # This function serves as a unit test for client code. It should raise
    # an error if the code is not behaving properly.

    # IMPORTANT:
    # The unit test must include an import statement to a Python modules the 
    # client is presumed to have supplied. This is the only way to access their code.
    
    # In this case, I am importing the Grid object assumed to be in functions.py.
    from functions import Grid

    # Create an object and use a method.
    grid = Grid()								
    grid.add_station('A', 2)						
    statA = grid.query_station('A')						

    # Check the query_station method is working correctly.
    assert(statA.id == 'A')							
    assert(statA.val == 2)

def test_simple_method():
    # load project
    proj = Project('example_project.zip', expecting = ['functions.py'])

    # Run a test function for all clients. The function must be defined within 
    # this script.
    proj.test('test_function')

    # If a client fails, a testing script is automatically written out.
    # E.g., deyodorie fails, producing failed_test_function/test_deyodorie_test_function.py

    # Failed test scripts can be run and debugged directly.
    # For example: 
    #   python test_deyodorie_test_function.py
    # will replicate the error.
    #
    # To fix the error, change 'self' to 'stat' on lines 42 and 43. Rerun 
    # the script to confirm the source of failure.

def test_method_specific_client():
    # load project
    proj = Project('example_project.zip', expecting = ['functions.py'])

    # Run the test function above for one client only.
    proj.test('test_function', client='deyodorie')

def test_method_multiprocessing():
    # load project
    proj = Project('example_project.zip', expecting = ['functions.py'])

    # Use simple multiprocessing to speed up testing.
    proj.test('test_function', ncpus = 2)

def test_and_summarise():
    # load project
    proj = Project('example_project.zip', expecting = ['functions.py','tasks.py'])

    # run the unit tests
    proj.test('test_function')

    # details of the test suite will be appended to the summary report
    proj.summarise('example_project.log')

if __name__ == "__main__":
    test_simple_method()

    #test_method_specific_client()

    #test_method_multiprocessing()
    
    #test_and_summarise()