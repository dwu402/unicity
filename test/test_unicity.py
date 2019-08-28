import sys
sys.path.append('..')

# BaseFile Class tests
def test_basefile_parse_lns():
    from unicity import BaseFile
    fl = BaseFile('test_file.py', zipfile=None)
    fp = open('test_file.py')
    lns = fp.readlines()
    fp.close()
    assert all([ln1==ln2 for ln1,ln2 in zip(lns,fl.lns)])

# PythonFile Class tests
def test_pythonfile_parse_lns():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    fp = open('test_file.py')
    lns = fp.readlines()
    fp.close()
    assert all([ln1==ln2 for ln1,ln2 in zip(lns,fl.lns)])
def test_pythonfile_parse_functions():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    functions = ['lu_read','lu_factor','lu_forward_sub','lu_backward_sub','zero_tol','isSquare']
    flkeys = fl.functions.keys()
    assert all([function in flkeys for function in functions])
def test_pythonfile_parse_imports():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    import_lines = [3,4,5]
    assert all([ln1==ln2 for ln1,ln2 in zip(import_lines,fl.import_lines)])
def test_pythonfile_parse_docstrings():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    assert fl.functions['zero_tol'].docstring is None
    assert all([fl.functions[k].docstring is not None for k in fl.functions.keys() if k is not 'zero_tol' ])
def test_pythonfile_parse_userfuncs():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    user_funcs = ['zero_tol','isSquare']
    flkeys = fl.functions['lu_factor'].user_funcs
    assert all([user_func in flkeys for user_func in user_funcs])
def test_pythonfile_parse_function_lineno():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    lns1 = fl.functions['lu_factor'].lineno
    lns2 = [60,160]
    assert all([ln1==ln2 for ln1,ln2 in zip(lns1,lns2)])
def test_pythonfile_parse_function_methods():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    lns1 = fl.functions['lu_factor'].methods
    lns2 = ['shape','arange','argmax']
    assert all([ln1==ln2 for ln1,ln2 in zip(lns1,lns2)])
def test_pythonfile_parse_function_funcs():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    lns1 = fl.functions['lu_factor'].funcs
    lns2 = ['isSquare','ValueError','print','print','print','print','print','print',
    'range','copy','abs','zero_tol','warn','range','range','print','print','print',
    'print','print','print']
    assert all([ln1==ln2 for ln1,ln2 in zip(lns1,lns2)])
def test_pythonfile_all_calls():
    from unicity import PythonFile
    fl = PythonFile('test_file.py', zipfile=None)
    all_calls1 = fl.get_calls('lu_factor')
    all_calls2 = {'isSquare':1,'ValueError':1,'print':12,'range':3,'copy':1,
        'abs':1,'zero_tol':1,'warn':1,'arange':1,'shape':1,'argmax':1}
    assert all([all_calls1[k]==all_calls2[k] for k in all_calls1.keys()])

# PNGFile Class test
def test_pngfile_metadata_load():
    from unicity import PNGFile
    from zipfile import ZipFile
    fl = PNGFile('thatchermargaret_file1.png',ZipFile('test_project_err.zip'))
    assert fl.author == 'thatchermargaret'

# Cohort Class tests
def test_cohort_load():
    from unicity import Cohort
    ch = Cohort('test_cohort2019.csv')
    name = ['bondjames','thatchermargaret','aquinasthomas','curiemarie']
    assert all([nm1 == nm2 for nm1,nm2 in zip(name, ch.name)])
    ids = [7,8,9]
    assert all([id1 == id2 for id1,id2 in zip(ids, ch.id)])
    emails = ['bondjames@gmail.com','thm@hotmail.com','aquinas@gmail.com','curie@gmail.com']
    assert all([email1 == email2 for email1,email2 in zip(emails, ch.email)])
    gpas = [4.7,6.2,5.9,9.0]
    assert all([gpa1 == gpa2 for gpa1,gpa2 in zip(gpas, ch.gpa)])

# Client Class tests
def test_client_load():
    from unicity import Cohort, Client
    ch = Cohort('test_cohort2019.csv')
    cl = Client('curiemarie', ch)
    assert cl.email == 'curie@gmail.com'
    assert cl.gpa == 9.0
    assert cl.id == 10
    assert cl.name == 'curiemarie'

# Project Class tests
def test_project_load():
    from unicity import Project
    dat = Project('test_project_load.zip')
    name = ['bondjames','thatchermargaret','curiemarie']
    assert all([nm in dat.client.keys() for nm in name])
    assert all (['file1.py' in cl.portfolio.files for cl in dat.client.values()])
def test_project_load_with_cohort():
    from unicity import Project
    dat = Project('test_project_load.zip', cohort='test_cohort2019.csv')
    ids = [7, 8, 10]
    names = ['bondjames','thatchermargaret','curiemarie']
    assert all([dat.client[name].id == idi for name,idi in zip(names,ids)])
    assert 'aquinasthomas' in [cl.name for cl in dat.absent]
def test_project_expecting():
    from unicity import Project
    expecting = ['file1.py']
    try:
        dat = Project('test_project_err.zip', expecting=expecting)
        raise
    except TypeError:
        pass
def test_project_ignore():
    from unicity import Project
    expecting = ['file1.txt']
    ignore = ['*.py','*.png']
    dat = Project('test_project_err.zip', expecting=expecting, ignore=ignore)
def test_project_check_completeness():
    from unicity import Project, Cohort
    expecting = ['file1.txt','file2.py']
    dat = Project('test_project_incomplete.zip', expecting=expecting, cohort='test_cohort2019.csv')
    assert dat.absent[0].name == 'aquinasthomas'
    assert dat.complete[0].name == 'bondjames'
    partial_names = [cl.name for cl in dat.partial]
    assert 'thatchermargaret' in partial_names
    assert 'curiemarie' in partial_names
    assert dat.partial[0].portfolio.missing[0] == 'file2.py'
    assert dat.partial[1].portfolio.missing[0] == 'file1.txt'
def test_project_compare():
    from unicity import Project
    import os
    dat = Project('test_project_load.zip', root = 'test')
    svfl = 'test_save.out'
    if os.path.isfile(svfl):
        os.remove(svfl)
    dat.compare_portfolios('file1.py/isSquare')
    assert os.path.isfile(svfl)
def test_project_compare_w_template():
    from unicity import Project
    import os
    template = 'file1.py'
    dat = Project('test_project_load.zip', root = 'test')
    svfl = 'test_save.out'
    if os.path.isfile(svfl):
        os.remove(svfl)
    dat.compare_portfolios('file1.py', template=template)
    assert os.path.isfile(svfl)    

# Test functions
def test_file_type():
    from unicity import File, PythonFile, TxtFile, PNGFile
    from zipfile import ZipFile
    zf = ZipFile('test_project_err.zip')
    assert type(File('bondjames_file1.py', zf)) is PythonFile
    assert type(File('thatchermargaret_file1.png', zf)) is PNGFile
    assert type(File('curiemarie_File_1.txt', zf)) is TxtFile
def test_repair_filename():
    from unicity import repair_filename
    expected_names = ['file1.txt']
    fl_repaired = repair_filename('file_1.txt',expected_names)
    assert fl_repaired == expected_names[0]
    fl_repaired2 = repair_filename('not_good_file_1.txt',expected_names)
    assert fl_repaired2 != expected_names[0]

if __name__ == "__main__":
    test_project_compare_w_template()