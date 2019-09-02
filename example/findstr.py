from unicity import Project 

def find_string():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py', 'tasks.py'])
    
    # Annie Alvis' submission contains the spelling 'connexion', which
    # is an unusual choice. Surely no one else has the same word...
    proj.findstr('connexion', verbose=True)

def find_string_in_location():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py', 'tasks.py'])
    
    # Direct unicity to only check within a specific routine in a 
    # specific file. Save the output to 'connexion.txt'.
    proj.findstr('connexion', location='functions.py/Grid.read', save='connexion.txt')

    # alternatives: 
    # - search within a file
    #proj.findstr('connexion', location='functions.py', save='connexion.txt')

    # - search within a class
    #proj.findstr('connexion', location='functions.py/Grid', save='connexion.txt')

    # - search within a function
    #proj.findstr('connexion', location='tasks.py/searchable_function', save='connexion.txt')

if __name__ == "__main__":
    find_string()

    #find_string_in_location()
    