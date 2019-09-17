# tests various combinations
import os,sys
sys.path.insert(0, os.path.abspath('..'))
from unicity import Project, Comparison 
from glob import glob
import os,traceback
import numpy as np

def test_function():
    from functions import Grid
    grid = Grid()								
    grid.add_station('A', 2)						
    statA = grid.query_station('A')						
    assert(statA.id == 'A')							
    assert(statA.val == 2)

def run_one(test, number = None):

    if number is not None:
        run_one(test[number])
        return

    # unpack
    proj_kwargs, compare_kwargs, report_kwargs, test_kwargs = test[1:]
    
    # similarity testing
    if test[0] == 1:
        proj = Project('../example/example_project.zip', **proj_kwargs)
        if compare_kwargs['prior_project'] is not None:
            compare_kwargs['prior_project'] = Project(compare_kwargs['prior_project'], proj_kwargs['expecting'])
        comp = proj.compare(**compare_kwargs)
        proj.similarity_report(comp, **report_kwargs)
    # unit testing
    elif test[0] == 2:
        proj = Project('../example/example_project.zip', **proj_kwargs)
        proj.test('test_function', **test_kwargs)
        
def assemble_tests():
    proj_kwargs = [
        ['expecting', ['functions.py',['functions.py','tasks.py']]],
        ['ignore', ['*']],
        ['cohort', [None, '../example/cohort.txt']], 
        ['root', [None,'test']],
    ]
    
    compare_kwargs = [
        ['routine',['functions.py/Roads.read','functions.py']], 
        ['metric',['command_freq','jaro']], 
        ['ncpus', [1,2]], 
        ['template', [None,'../example/functions_template.py']], 
        ['prior_project', [None,'../example/prior_project.zip']], 
    ]

    report_kwargs = [
        ['client', [None,'anon','amesarchie']], 
        ['save', [None,'test_save.png']],
    ]

    tests = []

    inds = []
    all_args = proj_kwargs+compare_kwargs+report_kwargs
    for i,item in enumerate(all_args):
        inds.append([i, len(item[1])])
    N = np.prod([ind[1] for ind in inds])
    Inds = np.zeros((len(all_args), N))
    for i, ni in inds:
        M = int(np.prod([ind[1] for ind in inds[i+1:]]))
        for j in range(i+1):
            for ini in range(ni):
                Inds[i,j*M*ni+ini*M:j*M*ni+(ini+1)*M] = ini

    i1 = len(proj_kwargs)
    i2 = i1 + len(compare_kwargs)
    for i in range(N):
        test = [
            1, 
            dict([[kt[0],kt[1][int(i)]] for kt,i in zip(proj_kwargs, Inds[:i1,i])]),
            dict([[kt[0],kt[1][int(i)]] for kt,i in zip(compare_kwargs, Inds[i1:i2,i])]),
            dict([[kt[0],kt[1][int(i)]] for kt,i in zip(report_kwargs, Inds[i2:,i])]),
            [],
            ]

        tests.append(test)

    return tests

def run_all_tests():

    tests = assemble_tests()

    fp = open('failed.log','w')
    # loop over tests
    for i, test in enumerate(tests):
        try:
            fls0 = glob('./*')
            # run test
            run_one(test)
            newfls = list(set(glob('./*')) - set(fls0))
            # remove files generated by test
            for fl in newfls: 
                os.remove(fl)
            # print outcome
            print('test {:d} - {}: passed'.format(i,test[0]))
        except:
            fp = open('failed.log','a')
            # if failed, don't remove files (may need for debugging)
            print('test {:d} - {}: FAILED'.format(i,test[0]))
            print(str(traceback.format_exc()))
            print(str(sys.exc_info()[0]))
            
            fp.write('test {:d} - {}: FAILED'.format(i,test[0])+'\n')
            fp.write(str(traceback.format_exc())+'\n')
            fp.write(str(sys.exc_info()[0])+'\n')
            fp.close()

if __name__ == "__main__":
    run_all_tests()