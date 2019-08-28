import os
from unicity.unicity import Project

# Canvas classes
class CanvasAssignment(Project):
    ''' Derived class for Canvas LMS.

        Parameters: (additional to Project class) 
        -----------
        repo_file : str
            File name containing address to git repository.
        repo_date : str
            Date string to pass to git checkout command. Pulls repository files that reflect most 
            recent commit prior to repo_date. Format 'YYYY-MM-DD HH:MM'.
        repo_user : str
            User name when pulling repository.
    '''
    def __init__(self, project, expecting = None, ignore = ['*'], cohort = None, root = None, repo_file = None, repo_date = None, repo_user = None, commit_messages = None):
        if repo_file is not None:
            expecting.append(repo_file)
            if repo_user is None:
                raise ValueError('require repo_user to download repo_file')
        super(CanvasAssignment,self).__init__(project, expecting, ignore, cohort, root)
        self._expecting = self._expecting[:-1]
        self._repo_file = repo_file
        self._repo_date = repo_date
        self._repo_user = repo_user
        self._get_repos(commit_messages)
    def _check_late(self, fl):
        ''' Overloaded method of Project.
        '''
        return 'late' in fl.split(os.sep)[-1]
    def _strip_meta(self, fl):
        ''' Overloaded method of Project.
        '''
        # pull off extension
        fl = fl.split(os.sep)[-1].split('.')
        ext = fl[-1]
        fl = '.'.join(fl[:-1])

        # remove prepended name and id data
        fl = fl.split('_')
        if 'late' in fl:
            fl = '_'.join(fl[4:])
        else:
            fl = '_'.join(fl[3:])

        # remove appended version information
        fl = fl.split('-')
        if len(fl) > 1:
            try:
                int(fl[-1])
                fl = fl[:-1]
            except ValueError:
                pass
        fl = '-'.join(fl)

        return fl + '.' + ext
    def check_control_sequence(self, controlfile, save=None):
        '''
        '''
        # parse control file
        cd = ControlFile(controlfile)
        # open save file
        if save is not None:
            fp = open(save,'w')
        # check for violations
        for seq in cd.sequences:
            violations = []
            for ps in seq.prior_seq:
                cl = self.findstr(ps)
                if len(cl)>0 and save is not None:
                    fp.write('sequence violations found for\n')
                    fp.write('{:s}\n'.format(ps))
                    for cli in cl: 
                        fp.write('{:s} ({:s})\n'.format(cli.name, cli.email))
                violations += cl
        return violations
    def _get_repos(self, commit_messages=None):
        from git import Repo, InvalidGitRepositoryError
        if self._repo_file is None:
            return

        if commit_messages is not None:
            fp = open(commit_messages,'w')

        for cl in self.clientlist:
            if self._repo_file not in cl.portfolio.files:
                continue

            ln = ''.join(cl.portfolio.files[self._repo_file].lns).rstrip()
            if 'https' in ln:
                rp = ln.split('https')[1]
            else:
                raise InvalidGitRepositoryError('repository address not recognized in file')
            rp = 'https://{:s}@'.format(self._repo_user)+rp.split('@')[-1]

            if not os.path.isdir('repos'):
                os.makedirs('repos')
                
            rdir = 'repos/{:s}'.format(cl.name)
            if not os.path.isdir(rdir):
                os.makedirs(rdir)
                try:
                    print('pulling repository for {:s} ({:s}) at address {:s}'.format(cl.name, cl.email, rp))
                    rp = Repo.clone_from(rp, 'repos/{:s}'.format(cl.name))
                    if self._repo_date is not None:
                        co = rp.git.rev_list('-n','1','--first-parent','--before','="{}"'.format(self._repo_date),'master')
                    rp.git.checkout(co)
                except:
                    print('could not clone {:s}'.format(cl.name))
                    continue
            else:
                try:
                    rp = Repo(rdir)
                except InvalidGitRepositoryError:
                    shutil.rmtree(rdir)
                    os.makedirs(rdir)
                    try:
                        print('pulling repository for {:s} ({:s}) at address {:s}'.format(cl.name, cl.email, rp))
                        rp = Repo.clone_from(rp, 'repos/{:s}'.format(cl.name))
                        if self._repo_date is not None:
                            co = rp.git.rev_list('-n','1','--first-parent','--before','="{}"'.format(self._repo_date),'master')
                        rp.git.checkout(co)
                    except:
                        print('could not clone {:s}'.format(cl.name))
                        continue
            
            # write commit messages to file
            if commit_messages is not None:
                N = len(list(rp.iter_commits('master')))
                fp.write('#{:s}, {:d} commits\n'.format(cl.name, N))
                fp.write("if True:\n")
                fp.write("    \'\'\'\n")
                for c in list(rp.iter_commits('master'))[::-1]:
                    fp.write('    -{:s}\n'.format(c.message.rstrip()))
                fp.write("    \'\'\'\n")

            for fl in self._expecting:
                flp = 'repos/{:s}/{:s}'.format(cl.name, fl)
                if os.path.isfile(flp):
                    cl.portfolio.files.update({fl:File(flp, None)})
        
        if commit_messages is not None:
            fp.close()

        # find which clients haven't submitted
        self._check_portfolio_status()
    def report_png_authorship(self):
        ''' Check PNG author metadata for uniqueness.

            PNG files must include 'author' or 'Author' as a pnginfo key.
        '''
        # read metadata
        md = {}
        for cl in self.clientlist:
            for fl in cl.portfolio.files.keys():
                if type(cl.portfolio.files[fl]) is PNGFile:
                    if cl.name not in md.keys():
                        md.update({cl.name:{}})
                    try:
                        md[cl.name].update({fl:cl.portfolio.files[fl].author})
                    except AttributeError:
                        continue
                    try:
                        md[cl.name].update({fl:cl.portfolio.files[fl].Author})
                    except AttributeError:
                        continue
        authors = []
        duplicated = []
        # check each client
        for cl in md.keys():
            for fl in md[cl].keys():
                if md[cl][fl] not in authors:
                    authors.append(md[cl][fl])
                elif md[cl][fl] not in duplicated:
                    duplicated.append(md[cl][fl])
                    print('metadata duplication: {:s}'.format(md[cl][fl]))
                    for cl in md.keys():
                        for fl in md[cl].keys():
                            if md[cl][fl] == duplicated[-1]:
                                print('- {:s}, {:s}'.format(cl, fl))
    def merge_files(self, fls, out, except_lines = None):
        ''' merges multiple Python files into single file
        '''
        if except_lines is not None:
            if type(except_lines) == str:
                except_lines = [except_lines,]
        for cl in self.clientlist:
            sfls = [fl for fl in fls if fl in list(cl.portfolio.files.keys())]
            fl0 = PythonFile(None, None)
            fl0.filename = out
            fl0.lns = []
            for sfl in sfls:
                fl0.lns += cl.portfolio.files[sfl].lns
            
            if except_lines is not None:
                for e in except_lines:
                    fl0.lns = [ln.replace(e,'') for ln in fl0.lns]
            cl.portfolio.files.update({out:fl0})
            continue            
    def _test_c(self, routine, ncpus, client, timeout, **kwargs):
        ''' Test suite for C files.
        '''
        ts = PythonFile(self._tsfile, None)
        for function in functions:
            ftest = 'test_'+function.split('.')[0]
            ts.prepare(ftest)
            assert (len(ts.functions[ftest].lineno) != 0), 'no unit test \'{:s}\' in \'test_suite.py\''.format(ftest)
            errs = []
            for client in self.clientlist:
                print(client.name)
                if function not in client.portfolio.files.keys():
                    errs.append(None)
                    continue

                fp = open(function, 'w')
                fp.writelines(client.portfolio.files[function].lns)
                fp.close()
                
                ilns = [ts.lns[iln-1].replace('\t','    ').rstrip()+'\n' for iln in ts.import_lines]
                i0, i1 = ts.functions[ftest].lineno
                utlns = [utln.replace('\t','    ').rstrip()+'\n' for utln in ts.lns[i0-1:i1-1]]
                
                lns = ilns + utlns
                lns.append('{:s}()'.format(ftest))
                errs.append(run_test(lns))
                            
            # write output as verbatim function with error traceback as docstring
            fail_file = self._get_file_name('fail', subtype=function.split('.')[0])
            errs = list(errs)
            fp = open(fail_file,'w')
            inds = range(len(self.clientlist))
            surnames = [sli.surname for sli in self.clientlist]
            firstnames = [sli.firstname for sli in self.clientlist]
            errs = [x for _,_,x in sorted(zip(surnames,firstnames,errs))]
            inds = [x for _,_,x in sorted(zip(surnames,firstnames,inds))]
            for ind, err in zip(inds, errs):
                client = self.clientlist[ind]
                if err is None:
                    # test suite not run due to syntax errors in tree
                    client.failed_test_suite = None
                    continue
                elif err == '':
                    # test suite passed - do not modify failure flag, unless not already defined
                    try:
                        client.failed_test_suite
                    except AttributeError:
                        client.failed_test_suite = False
                    continue
                # test suite failed, write function and traceback in docstring
                client.failed_test_suite = True
                fp.write('# {:s}\n'.format(cl.name_email))
                fp.write('if True:\n')            
                fp.write('    \'\'\'\n')
                fp.write('    '+err.replace('\n','\n    ')+'\n')
                fp.write('    \'\'\'\n')

            fp.close()
class ControlFile(object):
    ''' Class for managing control sequence files.
    '''
    def __init__(self, controlfile):
        self.controlfile = controlfile
        self.sequences = []
        self.load()
    def load(self):
        ''' Parse control sequence information from file.
        '''
        fp = open(self.controlfile,'r')
        lns = fp.readlines()
        fp.close()
        readingFile = True
        i = 0
        fl = lns[i].strip()
        i += 1
        while readingFile:
            if i == len(lns):
                readingFile = False
                break
            if lns[i].strip() == '':
                while lns[i].strip() == '':
                    i += 1
                    if i == len(lns):
                        readingFile = False
                        break
                if readingFile is False:
                    break

                fl = lns[i].strip()
                i += 1

            i_prior_seq = int(lns[i].strip())
            i += 1
            prior_seq = lns[i].strip()
            i += 1
            i_seq = int(lns[i].strip())
            i += 1
            seq = lns[i].strip()
            i += 1
            self.sequences.append(ControlSequence(file = fl, seq = seq, prior_seq = prior_seq))
class ControlSequence(object):
    ''' Class for managing control sequences.
    '''
    def __init__(self, file, seq, prior_seq):
        self.file = file
        self.seq = seq
        if type(prior_seq) is not list:
            prior_seq = [prior_seq,]
        self.prior_seq = prior_seq
        # sanity check
        for pseqi in self.prior_seq:
            assert (self.seq not in pseqi), 'control sequence \'{:s}\' present in prior control sequences'.format(self.seq)
