
import sys
sys.path.append(r'E:\code\unicity')
from unicity.unicity import Project, Comparison 

def dump_docstrings():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    
    # output docstrings
    proj.dump_docstrings('function.py/NetworkNZ.read_network', save = 'read_network.py')

if __name__ == "__main__":
    dump_docstrings()
    