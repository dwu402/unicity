
import sys
sys.path.append(r'D:\code\unicity')
from unicity.unicity import Project 

def load_project():
    # load a Project from a zip file, tell unicity to look for
    # generic files 'functions.py' and 'tasks.py')
    proj = Project('example_project.zip', expecting=['functions.py', 'tasks.py'])
    
    # print a summary report of the project
    proj.summarise('example_project.log')

def load_project_with_cohort_file():
    # cohort CSV files contain information about expected clients
    # column headers are used to populate client attributes   
    proj = Project('example_project.zip', cohort='cohort.txt', expecting=['functions.py', 'tasks.py'])
    
    # if cohort file contains 'email' column, this information
    # will be included in the summary
    proj.summarise('example_project.log')

def load_project_from_folder():
    # projects can be loaded from folders the same as zip files   
    # (extract example_project.zip before running this command)
    proj = Project('example_project', expecting=['functions.py', 'tasks.py'])
    
    proj.summarise('example_project.log')

if __name__ == "__main__":
    load_project()

    #load_project_with_cohort_file()

    #load_project_from_folder()
    