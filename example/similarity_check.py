
import sys
sys.path.append(r'D:\code\unicity')
from unicity.unicity import Project 

def similarity_check():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check on one function
    comp = proj.compare('functions.py/NetworkNZ.read_network')
    # plot similarity check
    proj.similarity_report(comp)

def similarity_check_with_template():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check on whole file, using template file and 2 cpus
    comp = proj.compare('functions.py', template='functions_template.py', ncpus=2)
    # plot anonymised similarity check
    proj.similarity_report(comp, client = 'anon', save = 'report_w_template.png')

if __name__ == "__main__":
    similarity_check()
    
    similarity_check_with_template()