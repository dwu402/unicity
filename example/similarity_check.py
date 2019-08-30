from unicity import Project, Comparison 

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

def similarity_check_prior_project():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # load a previous Project
    prior_proj = Project('prior_project.zip', expecting=['functions.py'])
    # run similarity check on whole file, using template file and 2 cpus
    comp = proj.compare('functions.py/NetworkNZ.read_network', prior_project=prior_proj)
    # plot anonymised similarity check
    proj.similarity_report(comp)
    
def similarity_check_jaro():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check using Jaro distance between strings
    comp = proj.compare('functions.py', metric='jaro', template = 'functions_template.py')
    # plot similarity check
    proj.similarity_report(comp)

def save_and_load_comparisons():
    # load Projects
    proj = Project('example_project.zip', expecting=['functions.py'])
    prior_proj = Project('prior_project.zip', expecting=['functions.py'])
    # run similarity check on one function
    comp = proj.compare('functions.py/NetworkNZ.read_network', prior_project=prior_proj)
    # save the comparison object
    comp.save('example_project.dat')
    # load the comparison object (passing prior project, if applicable)
    comp_loaded = Comparison('example_project.dat', prior_project = prior_proj)
    # plot similarity check
    proj.similarity_report(comp_loaded)

if __name__ == "__main__":
    similarity_check()
    
    #similarity_check_with_template()

    #similarity_check_prior_project()
    
    #similarity_check_jaro()

    #save_and_load_comparisons()