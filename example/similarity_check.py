from unicity import Project, Comparison 

def similarity_check():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check on one function
    comp = proj.compare('functions.py/Roads.read')
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
    comp = proj.compare('functions.py/Roads.read', prior_project=prior_proj)
    # plot anonymised similarity check
    proj.similarity_report(comp)
    
def similarity_check_jaro():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check using Jaro distance between strings
    comp = proj.compare('functions.py', metric='jaro', template = 'functions_template.py')
    # plot similarity check
    proj.similarity_report(comp)
    
def similarity_check_moss():
    # load a Project
    proj = Project('example_project.zip', expecting=['functions.py'])
    # run similarity check using MOSS plagiarism algorithm
    comp = proj.compare('functions.py', metric='moss', template = 'functions_template.py')
    # plot similarity check
    proj.similarity_report(comp)

def save_and_load_comparisons():
    # load Projects
    proj = Project('example_project.zip', expecting=['functions.py'])
    prior_proj = Project('prior_project.zip', expecting=['functions.py'])
    # run similarity check on one function
    comp = proj.compare('functions.py/Roads.read', prior_project=prior_proj)
    # save the comparison object
    comp.save('example_project.dat')
    # load the comparison object (passing prior project, if applicable)
    comp_loaded = Comparison('example_project.dat', prior_project = prior_proj)
    # plot similarity check
    proj.similarity_report(comp_loaded)

def similarity_check_matlab():
    # load MATLAB Project
    mfls = ['brent','bisection','combined','golden','laguerre','newton','newtonmultivar','regularafalsi','secant']
    mfls = [mfl+'.m' for mfl in mfls]
    proj = Project('example_project_matlab.zip', expecting=mfls)
    
    # run similarity check on file
    comp = proj.compare('combined.m', metric = 'moss', template = 'matlab_template.zip')

    # plot similarity check
    proj.similarity_report(comp)

def similarity_check_wildcard():
    # load MATLAB Project
    mfls = ['brent','bisection','combined','golden','laguerre','newton','newtonmultivar','regularafalsi','secant']
    mfls = [mfl+'.m' for mfl in mfls]
    proj = Project(r'C:\Users\ddem014\Downloads\331 Lab 1 2019.zip', expecting=mfls)

    # run similarity check using WILDCARD to concatenate multiple files
    comp = proj.compare('*i*.m')
    
    # plot similarity check
    proj.similarity_report(comp)

if __name__ == "__main__":
    similarity_check()
    
    #similarity_check_with_template()

    #similarity_check_prior_project()
    
    #similarity_check_jaro()
    
    #similarity_check_moss()

    #save_and_load_comparisons()

    #similarity_check_matlab()

    #similarity_check_wildcard()

    