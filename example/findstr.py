from unicity import Project 

def find_string():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py', 'tasks.py'])
    
    # Annie Alvis' submission contains the word 'floders', which
    # is an unusual typo. Surely no one else has the same one...
    proj.findstr('floders', verbose=True)

def find_string_in_location():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py', 'tasks.py'])
    
    # Direct unicity to only check within a specific routine in a 
    # specific file. Save the output to 'floders.txt'.
    proj.findstr('floders', location='functions.py/NetworkNZ.read_network', save='floders.txt')

    # alternatives: 
    # - search within a file
    #proj.findstr('floders', location='functions.py', save='floders.txt')

    # - search within a class
    #proj.findstr('floders', location='functions.py/NetworkNZ', save='floders.txt')

    # - search within a function
    #proj.findstr('floders', location='tasks.py/searchable_function', save='floders.txt')

if __name__ == "__main__":
    find_string()

    #find_string_in_location()
    