import sys
sys.path.append(r'E:\code\unicity')
from unicity.unicity import Project 

def test_function():
    # This function serves as a unit test for client code. It should raise
    # an error if the code is not behaving properly.

    # IMPORTANT:
    # The unit test must include an import statement to a Python modules the 
    # client is presumed to have supplied. This is the only way to access their code.
    
    # In this case, I am importing the Network object from functions.py.
    from functions import Network

    # Create an object and use a method.
    network = Network()								
    network.add_node('A', 2)						
    ndA = network.get_node('A')						

    # Check the add_node method is working correctly.
    assert(ndA.name == 'A')							
    assert(ndA.value == 2)

def test_simple_method():
    # load project
    proj = Project('example_project.zip', expecting = ['functions.py'])

    # Run a test function for all clients. The function must be defined within 
    # this script.
    proj.test('test_function')

    # If a client fails, a testing script is automatically written out.
    # E.g., deyodorie fails, producing failed_test0/test_deyodorie_test0.py

    # Failed test scripts can be run and debugged directly.
    # For example: 
    #   python test_deyodorie_test0.py
    # will replicate the error.
    #
    # To fix the error, change 'self' to 'node' on lines 76 and 77. Rerun 
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

if __name__ == "__main__":
    test_simple_method()

    #test_method_specific_client()

    #test_method_multiprocessing()