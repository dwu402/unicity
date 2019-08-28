import os, ast, zipfile, sys, traceback, re, shutil, glob
import numpy as np
from itertools import groupby, starmap
from functools import partial
from copy import copy
from itertools import chain
from multiprocessing import Pool, Process, Manager
from matplotlib import pyplot as plt
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform
from fuzzywuzzy import fuzz
from PIL import Image
from fnmatch import fnmatch
from difflib import SequenceMatcher
Image.MAX_IMAGE_PIXELS = 1000000000
pypdf_import_fail = False
try: 
    from PyPDF2 import PdfFileReader, PdfFileWriter
except:
    try:
        from pyPdf import PdfFileReader, PdfFileWriter
    except:
        pypdf_import_fail = True

# to do list:
# - comparisons to prior years
# - move summary of test output to new file
# - other distance metrics: permutation vs. combination
# - check for find-replace evidence in comments
# - does similarity metric need to be collapsed for smaller code samples? i.e.,
#   similarity of long code weighted more than similarity of short code?

# General classes
class Portfolio(object):
    ''' Class for individual client file collection.
    '''
    def __init__(self):
        self.files = {}
        self.late = False
        self.missing = []
class Cohort(object):
    ''' Class for all clients in a cohort.

        Parameters:
        -----------
        filename : str
            Path to file containing cohort information. 

        Notes:
        ------
        Cohort file should contain client information in CSV format. The first row
        defines column names and must at least contain a 'name' column. Client information
        is given on separate rows.
        
        For example, the contents of 'cohort.csv'

        name, id, email, gpa
        bondjames, 007, bondjames@gmail.com, 4.7
        thatchermargaret, 008, thm@hotmail.com, 6.2
        aquinasthomas, 009, aquinas@gmail.com, 5.9
        curiemarie, 010, curie@gmail.com, 9.0

        define a cohort of four clients. Each column is provisioned as a separate attribute 
        of the Cohort object.
    '''
    def __init__(self, filename):
        self.filename = filename
        self.parse_year()
        self.load()
    def __repr__(self):
        try:
            return '{:d}cohort'.format(self.year)
        except AttributeError:
            return 'cohort'
    def parse_year(self):
        ''' Attempts to parse year information from cohort file path.
        '''
        yrs = re.findall('(\d{4})', self.filename)
        if len(yrs) == 0:
            self.year = None
        else:
            self.year = int(max(set(yrs), key=yrs.count))
    def load(self):
        ''' Load cohort data.
        '''
        if not os.path.isfile(self.filename):
            raise FileNotFoundError('cannot find cohort file at \'{:s}\''.format(self.filename))
        fp = open(self.filename,'r')
        hdrs = fp.readline().rstrip()
        lns = fp.readlines()
        lns = [ln.strip() for ln in lns if ln.strip != '']
        hdrs = [hdr.strip() for hdr in hdrs.split(',')]
        if 'name' not in hdrs:
            raise ValueError('cohort file \'{:s}\' must contain \'name\' column'.format(self.filename))
        
        n = len(lns)
        vals = [n*[None] for hdr in hdrs]

        # parse values
        for j,ln in enumerate(lns):
            val = ln.split(',')
            for i,vali in enumerate(val):
                vals[i][j] = vali.strip()
        
        # value type conversion
        for i in range(len(vals)):
            try:
                # attempt to convert to float
                vals[i] = [float(vali) for vali in vals[i]]
                # attempt to convert float to integer
                if all([abs(int(vali)-vali)<1.e-8 for vali in vals[i]]):
                    vals[i] = [int(vali) for vali in vals[i]]
            except ValueError:
                # must be string
                pass

        # save data as object attributes
        for hdr,val in zip(hdrs,vals):
            self.__setattr__(hdr, val)
        self.columns = hdrs
class Client(object):
    ''' Class for individual client.

        Notes:
        ------
        When created by a Project object with an associated cohort file, Client
        objects are provisioned attributes corresponding to column information
        in the cohort file.
    '''
    def __init__(self, name, cohort=None):
        # populate with unique client info 
        self.name = name
        if cohort is not None:
            i = cohort.name.index(name)
            for col in cohort.columns:
                if col == 'name':
                    continue
                self.__setattr__(col, cohort.__getattribute__(col)[i])
        # setup other attributes
        self.cs_score = 0
        self.portfolio = Portfolio()
    def __repr__(self):
        return 'cl:'+self.name
    @property
    def name_email(self):
        try:
            return '{:s} ({:s})'.format(self.name, self.email)
        except AttributeError:
            return '{:s}'.format(self.name)
class Comparison(object):
    def __init__(self, loadfile=None):
        if loadfile is not None:
            self._load(loadfile)
    def __repr__(self):
        return 'compare: {:s} by {:s}'.format(self.routine, self.metric)
    def _plot(self, proj, savefile, client):
        ''' Plot comparison matrix.

            Notes
            -----
            Implementation from https://stackoverflow.com/questions/2982929/plotting-
            results-of-hierarchical-clustering-ontop-of-a-matrix-of-data-in-python

        '''
        # load data
        D = self.matrix
        
        # process distance matrix
        n = len(proj.clientlist)
        k = 0; Ds = np.zeros(int((n-1)*n/2))
        for i in range(n):
            for j in range(i+1,n):
                D[j,i] = D[i,j]
                Ds[k] = D[i,j]
                k+=1
        # minimum similarity score for each client
        Dmin = np.zeros(n)
        Dmin[1:-1] = [np.min([np.min(D[i,:i]), np.min(D[i,i+1:])]) for i in range(1,n-1)]
        Dmin[0] = np.min(D[0,1:])
        Dmin[-1] = np.min(D[-1,:-1])
        condensedD = squareform(D)
        Y1 = sch.linkage(condensedD, method='centroid')
        Y2 = sch.linkage(condensedD, method='single')
        
        # figure and axis set up
        fig = plt.figure(figsize=(8.27,11.69 ))
        ax0 = fig.add_axes([0,0,1,1])
        ax1 = fig.add_axes([0.10,0.1+0.6*0.29,0.11,0.6*0.71])
        ax1b = fig.add_axes([0.205,0.1+0.6*0.29,0.09,0.6*0.71])
        ax2 = fig.add_axes([0.3,0.705 +0.09*0.71,0.6,0.19*0.71])
        ax2b = fig.add_axes([0.3,0.705,0.6,0.09*0.71])
        axmatrix = fig.add_axes([0.3,0.1+0.6*0.29,0.6,0.6*0.71])
        axbar = fig.add_axes([0.1, 0.1, 0.8, 0.15])
        
        # plotting
        Z1 = sch.dendrogram(Y1, orientation='left', ax=ax1)
        ax1.set_xlim([1.05,0])
        Z2 = sch.dendrogram(Y2, ax=ax2)
        ax2.set_ylim([0,1.05])
        idx1 = Z1['leaves']
        idx2 = Z2['leaves']
        # get client similarity if requested
        if client not in [None, 'anon']:
            ix = [i for i,cl in enumerate(proj.clientlist) if cl.name == client][0]
            max_similarity = np.min([D[j,ix] for j in range(D.shape[0]) if j!= ix])
        # shuffle matrix for clustering
        D = D[idx1,:]
        D = D[:,idx2]
        im = axmatrix.matshow(D, aspect='auto', origin='lower', cmap=plt.cm.YlGnBu, vmin=0, vmax=1.)
        # plot all similarities
        bins = np.linspace(0,1,max([int(np.sqrt(len(Ds))/2),2]))
        h,e = np.histogram(Ds, bins = bins)
        w = e[1]-e[0]
        m = 0.5*(e[:-1]+e[1:])
        h = h/np.sum(h[:-1])/w
        axbar.bar(m[:-1], h[:-1], w, color = [plt.cm.YlGnBu(i) for i in m], label='full distribution')
        axbar.set_xlabel('uniqueness')
        axbar.set_yticks([])
        # plot minimum similarities
        h,e = np.histogram(Dmin, bins = bins)
        h = h*n/2.
        w = e[1]-e[0]
        m = 0.5*(e[:-1]+e[1:])
        h = h/np.sum(h[:-1])/w
        axbar.bar(m[:-1], h[:-1], w, edgecolor = 'k', fc = (0,0,0,0), label='distribution of minimums')
        # find best fit GEV curve
        from scipy.optimize import curve_fit
        from scipy.stats import genextreme
        
        try:
            pcut = 0.0
            i = np.argmin(abs(m-pcut))
            scale = np.sum(h[:-1])/np.sum(h[i:-1])
            p = curve_fit(gev, m[i:-1], h[i:-1]*scale, [0.,0.1],
                bounds = ([0,0],[np.inf,np.inf]))[0]
            x1 = np.linspace(0,1,101)
            axbar.plot(x1, gev(x1, *p), 'r:', label='best-fit Weibull')
        except:
            axbar.plot([], [], 'r:', label='Weibull fitting failed')
            pass

        gridlines = 20
        dn = int(n/gridlines)
        if not dn: dn = 1

        # upkeep
        for ax in [ax1, ax2, axmatrix]:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlim(auto=False)
            ax.set_ylim(auto=False)
        
        for axb,ax in zip([ax1b, ax2b],[ax1,ax2]):
            axb.axis('off')
            axb.set_xlim(ax.get_xlim())
            axb.set_ylim(ax.get_ylim())

        # grid lines and client names
        dy = ax1b.get_ylim()[1]/n
        x0 = ax1b.get_xlim()[1]
        for i,idx in enumerate(Z1['leaves']):
            name = proj.clientlist[idx].name
            col = 'k'
            if client is not None:
                if name != client:
                    name = '*'*np.random.randint(10,15)
                else:
                    col = 'r'
                
            ax1b.text(0.9*x0, (i+0.5)*dy, name, size=5, color = col, ha='right', va='center')
            if i % dn == 0:
                ax1b.axhline(i*dy, color = 'k', linestyle='-', linewidth=0.25)
                ax1.axhline(i*dy, color = 'k', linestyle='-', linewidth=0.25)

        dx = ax2b.get_xlim()[1]/n
        y0 = ax2b.get_ylim()[0]
        for i,idx in enumerate(Z2['leaves']):
            name = proj.clientlist[idx].name
            col = 'k'
            if client is not None:
                if name != client:
                    name = '*'*np.random.randint(10,15)
                else:
                    col = 'r'
                    lbl = 'score - {:3.2f}'.format(max_similarity)
                    axbar.axvline(max_similarity,color='r',linestyle = '-', label=lbl)
            axbar.legend()
                
            ax2b.text((i+0.5)*dx, 0.95*y0, name, size=5, color = col, ha='center', 
                va='bottom', rotation=-90.)
            if i % dn == 0:
                ax2b.axvline(i*dx, color = 'k', linestyle='-', linewidth=0.25)
                ax2.axvline(i*dx, color = 'k', linestyle='-', linewidth=0.25)

        for i in range(n):
            if i % dn == 0:
                axmatrix.axvline(i-0.5, color = 'k', linestyle='-', linewidth=0.25)
                axmatrix.axhline(i-0.5, color = 'k', linestyle='-', linewidth=0.25)

        # set title
        ax0.axis('off')
        ax0.patch.set_alpha(0)
        ax0.text(0.5,0.95, 'comparing {:s} by {:s}'.format(self.routine, self.metric), ha = 'center', va = 'top')
        fig.savefig(savefile, dpi = 500)
        plt.close(fig)
    def _load(self, loadfile):
        ''' Loads a precomputed comparison file.
        '''
        fp = open(loadfile,'r')
        ln = fp.readline().strip().split()
        n = int(ln[0])
        self.routine = ln[1]
        self.metric = ln[2]
        fp.close()
        # read matrix
        self.matrix = np.genfromtxt(loadfile, skip_header=1)
    def save(self, savefile):
        ''' Saves a precomputed comparison file.

            Parameters:
            -----------
            savefile : str
                Name of file to save comparison matrix.
        '''
        fp = open(savefile,'w')
        n = self.matrix.shape[0]
        # header data
        fp.write('{:d} '.format(n))                                  # number of clients
        fp.write((' {:s} {:s}').format(self.routine, self.metric))
        fp.write('\n')
        for i in range(n):
            for j in range(n):
                fp.write('{:4.3f} '.format(self.matrix[i,j]))
            fp.write('\n')
        fp.write('\n')
        fp.close()
class Project(object):
    ''' Class for all client portfolios.

        Parameters:
        -----------
        project : str
            Path to folder or zip archive containing client portfolios.
        expecting : list (optional)
            List of expected file names in each portfolio.
        ignore : list (optional)
            List of file names to ignore (unix identifiers fine).
        cohort : str (optional)
            Path to file containing information about clients. See Cohort object.
        root : str (optional)
            String for naming of output files.
        
        Attributes:
        -----------
        client : dict
            Dictionary of Client objects, keyed by client name.
        clientlist : list
            List of Client objects, ordered alphabetically by client name.
        cohort : Cohort
            Object containing cohort information.
        portfolio_status : dict
            Contains completeness information about individual client portfolios.
        test_status : dict

        
        Methods:
        --------
        compare
        dump_docstrings
        findstr
        similarity_report
        summarise
        test
    '''
    def __init__(self, project, expecting, ignore = ['*'], cohort = None, root = None):
        project = os.path.abspath(project)
        if os.path.isdir(project):
            self._projdir = project
            self._projzip = None
        elif zipfile.is_zipfile(project):
            self._projzip = project
            self._projdir = None
        else:
            raise ValueError("unrecognized project type \'{:s}\'".format(project))
        
        self._root = root
        if cohort is not None:
            self.cohort = Cohort(cohort)
        else:
            self.cohort = None
        self._parse_filepath()
        self._expecting = expecting
        self._ignore_files = ignore
        self._run_test = False
        self.clientlist = []
        self.client = {}
        self.portfolio_status = {'complete':[],'partial':[],'absent':[]}
        # test attributes
        self.test_status = {'absent portfolio':[],'missing file':[],'compile error':[],
            'missing routine':[],'failed':[],'passed':[]}
        
        # comparison attributes
        self._load()
    def _parse_filepath(self):
        ''' Separates off working directory and root file name.
        '''
        if self._projdir is not None:
            self._work_dir = os.sep.join(self._projdir.split(os.sep)[:-1])
        else:
            self._work_dir = os.path.dirname(self._projzip)
        if self._root is None:
            if self._projdir is not None:
                self._root = self._projdir.split(os.sep)[-1]
            else:
                self._root = os.path.splitext(os.path.basename(self._projzip))[0]
    def _get_file_name(self, filetype, subtype = None):
        ''' Returns file names based on work dir and root.
        '''
        fl = self._work_dir+os.sep+self._root
        fl += '_'+filetype
        if subtype is not None:
            fl += '_'+subtype
        if filetype == 'save':
            fl += '.out'
        elif filetype == 'plot':
            fl += '.png'
        elif filetype == 'log':
            fl += '.log'
        elif filetype == 'fail':
            fl += '.py'
        return fl
    def _ignore(self, fl):
        ''' Check whether file name conforms to ignore patterns.
        '''
        # return on wildcard matches
        for ifl in self._ignore_files:
            if fnmatch(fl, ifl):
                return
        # return on template matches
        if max([check_fuzzy_ratio(fl, ignore) for ignore in self._ignore_files])>75:
            return
        # raise error
        raise TypeError('unexpected file: {:s}'.format(fl.split(os.sep)[-1]))
    def _load(self):
        ''' Parse zipfile containing portfolios.
        '''
        # scan file for client names
        if self._projdir is not None:
            zf = None
            fls = glob.glob(self._projdir+os.sep+'*')
        else:
            zf = zipfile.ZipFile(self._projzip)
            fls = [fl.filename for fl in zf.filelist]
        for fl in fls:
            client = self._parse(fl)       # get corresponding client
            client.late = self._check_late(fl)

            # fuzzy string matching because people can't follow instructions
            ratios = [check_fuzzy_ratio(fl, expect) for expect in self._expecting]

            # accept above (arbitrary) threshold
            if max(ratios)>75:
                fl0 = self._expecting[np.argmax(ratios)]
            else:
                # check against ignore list
                self._ignore(fl)
                continue 

            client.portfolio.files.update({fl0:File(fl, zf)})            # save file information
        
        # sort clients alphabetically 
        self.clientlist = sorted(self.clientlist, key = lambda x: x.name)

        # find which clients haven't submitted
        self._check_portfolio_status()
    def _parse(self, fl):
        ''' Return client object corresponding to file name.
        '''
        name = fl.split(os.sep)[-1].split('_')[0]
        try:
            return self.client[name]
        except KeyError:
            
            if self.cohort is not None:
                if name not in self.cohort.name:
                    raise ValueError("client '{}' from file '{}' not in cohort file '{}'".format(
                        name, fl, self.cohort.filename 
                    ))

            cl = Client(name, self.cohort)
            self.clientlist.append(cl)
            self.client.update({cl.name:cl})
            return cl
    def _strip_meta(self, fl):
        ''' Removes file name decorators and returns base name.

            Parameters:
            -----------
            fl : str
                file name with decorators

            Returns:
            --------
            str
                file name with decorators removed

            Notes:
            ------
            Overload this method when for custom application.
        '''
        # pull off extension
        fl = fl.split('.')
        ext = fl[-1]
        fl = '.'.join(fl[:-1])

        # remove prepended name and id data
        fl = fl.split('_')[1]

        return fl + '.' + ext
    def _check_late(self, fl):
        ''' Check if file name indicates late portfolio.

            Parameters:
            -----------
            fl : str
                file name with decorators

            Returns:
            --------
            bool
                True flag indicates file was submitted late

            Notes:
            ------
            Overload this method for custom application. Default implementation
            assumes no files are late.
        '''
        return False
    def _check_portfolio_status(self):
        ''' Compile portfolio completeness information.
        '''
        # clients with absent portfolios (if cohort info available)
        if self.cohort is not None:
            submitted = self.client.keys()
            self.portfolio_status['absent'] = [Client(name, self.cohort) for name in self.cohort.name if name not in submitted]
        
        # clients with partial portfolios (if expecting defined)
        if self._expecting is None:
            return

        for cl in self.clientlist:
            # partial portfolios (missing files)
            cl.portfolio.missing = list(set(self._expecting) - set(cl.portfolio.files.keys()))
            if len(cl.portfolio.missing) > 0:
                self.portfolio_status['partial'].append(cl)
            # complete portfolios (no missing files)
            else:
                self.portfolio_status['complete'].append(cl)
    def _check_test_status(self):
        ''' Summarises results of the test suite.
        '''
        for cl in self.clientlist:
            # check if test suite has been run on client
            try:
               cl.failed_test_suite
            except AttributeError:
                self.test_status['absent portfolio'].append(cl)
                continue
            # check for
            if cl.failed_test_suite == -1:
                # no file
                self.test_status['missing file'].append(cl)
            elif cl.failed_test_suite == -2:
                # no routine
                self.test_status['missing routine'].append(cl)
            elif cl.failed_test_suite == -3:
                # syntax errors in code
                self.test_status['compile error'].append(cl)
            elif cl.failed_test_suite:
                # failed test suite
                self.test_status['failed'].append(cl)
            elif not cl.failed_test_suite:
                # passed test suite
                self.test_status['passed'].append(cl)
    # analysis methods
    def findstr(self, string, location=None, verbose = False, save=None):
        ''' Check portfolio for instances of string.

            Parameters:
            -----------
            string : str
                String to locate in portfolios.
            location : str (optional)
                Search limited to particular file, class or routine, specified in unicity format
                *file*, *file*/*function*, or *file*/*class*.*method*.
            verbose : bool (optional)
                Flag to print discovered strings to screen (default False).
            save : str (optional)
                File to save results of string search.

            Returns:
            --------
            found_clients : list
                Client objects whose portfolios contain the search string.

        '''
        fl,obj,func = split_at_delimiter(location)
        if obj is not None:
            func = obj + '.' + func
        if save is not None:
            fp = open(save, 'w')
        # loop over clients in order
        found_clients = []
        for cl in self.clientlist:
            written_name = False
            # extract lines filtered by file or routine
            for fln,fli in cl.portfolio.files.items():
                written_file = False
                # logic to narrow search field
                if fl is None:
                    # case 1 - search all files for string
                    lns = fli.lns
                    ilns = np.arange(1, len(lns)+1)
                elif fln != fl:
                    # case 2 - search in specific file, this isn't it
                    continue
                elif func is None:
                    # case 3 - search in specific file, search entire file
                    lns = fli.lns
                    ilns = np.arange(1, len(lns)+1)
                elif fli.tree == -1:
                    # case 4 - search in specific routine, syntax compile errors
                    continue
                elif func not in fli.functions:
                    # case 5 - search in specific routine, routine not present
                    continue
                else:
                    # case 6 - search in specific routine
                    lns = fli.functions[func].lns
                    i0,i1 = fli.functions[func].lineno
                    ilns = np.arange(i0+1, i1+2)

                # execute search
                for iln,ln in zip(ilns, lns):
                    if string in ln:
                        # student header info
                        if not written_name:
                            found_clients.append(cl)
                            outstr = cl.name
                            if verbose:
                                print(outstr)
                            if save is not None:
                                fp.write(outstr+'\n')
                            written_name = True
                        # file header info
                        if not written_file:
                            outstr = 'in file: {:s}'.format(fln)
                            if verbose:
                                print(outstr)
                            if save is not None:
                                fp.write(outstr+'\n')
                            written_file = True
                        # discovery info
                        outstr = '{:4d}>'.format(iln)+ln.rstrip().replace('\t','    ')
                        if verbose:
                            print(outstr)
                        if save is not None:
                            fp.write(outstr+'\n')

        if save is not None:
            fp.close()
        return found_clients
    def summarise(self, summaryfile, verbose=False):
        ''' Create log file with portfolio information.
        '''
        self._check_test_status()
        # open log file
        fp = open(summaryfile, 'w')
        fline = (80*"-")+'\n'

        # header
        fp.write("Portfolio information for {:s}\n".format(self._root))
        fp.write(fline)
        fp.write('\n')

        # high-level, highlighting missing or incomplete portfolios
        fp.write(fline)
        fp.write("SUMMARY\n")
        fp.write(fline)
        if self.cohort is not None:
            fp.write("{:s}: {:d} clients\n".format(self.cohort.filename, len(self.cohort.name)))
        else:
            fp.write("cohort: {:d} clients\n".format(len(self.clientlist)))
        fp.write('-----\n')
        fp.write('{:d} clients with complete portfolios\n'.format(len(self.portfolio_status['complete'])))
        fp.write('{:d} clients with partial portfolios\n'.format(len(self.portfolio_status['partial'])))
        if self.cohort is not None:
            fp.write('{:d} clients with absent portfolio\n'.format(len(self.portfolio_status['absent'])))
        
        if self._run_test:
            fp.write('-----\n')
            fp.write('{:d} clients passed the test suite\n'.format(len(self.test_status['passed'])))
            fp.write('{:d} clients failed the test suite\n'.format(len(self.test_status['failed'])))
            fp.write('{:d} clients did not have function (no test run)\n'.format(len(self.test_status['missing routine'])))
            fp.write('{:d} clients had syntax errors (no test run)\n'.format(len(self.test_status['compile error'])))
            fp.write('{:d} clients had no file (no test run)\n'.format(len(self.test_status['missing file'])))
        
        fp.write('\n')

        # more information about incomplete portfolios
        if len(self.portfolio_status['partial']) != 0:
            fp.write(fline)
            fp.write("PARTIAL PORTFOLIOS\n")
            fp.write(fline)
            for cl in self.portfolio_status['partial']:
                fp.write('{:s}, missing '.format(cl.name_email))
                fp.write((len(cl.portfolio.missing)*'{:s}, ').format(*(cl.portfolio.missing))[:-2]+'\n')
            fp.write('\n')

        # more information about absent portfolios
        if len(self.portfolio_status['absent']) != 0:
            fp.write(fline)
            fp.write("ABSENT PORTFOLIOS\n")
            fp.write(fline)
            for cl in self.portfolio_status['absent']:
                fp.write('{:s}\n'.format(cl.name_email))
            fp.write('\n')

        # more information about failed tests, syntax errors, absent tests
        reports = [
            ['failed','FAILED TEST SUITE'],
            ['missing file',"FILE NOT INCLUDED IN PORTFOLIO"],
            ['missing routine',"TEST FUNCTION NOT INCLUDED IN FILE"],
            ['compile error',"SYNTAX ERRORS DURING COMPILE"],
            ]
        for key, msg in reports:
            if len(self.test_status[key]) != 0:
                fp.write(fline)
                fp.write("{:s}\n".format(msg))
                fp.write(fline)
                for cl in self.test_status[key]:
                    fp.write('{:s}\n'.format(cl.name_email))
                fp.write('\n')
        fp.close()

        # optional print to screen
        if verbose:
            with open(summaryfile, 'r') as fp:
                lns = fp.readlines()
            
            for ln in lns:
                print(ln.strip())
    def dump_docstrings(self, routine, save):
        ''' Writes docstring information out to file.

            Parameters:
            -----------
            routine : str
                callable sequence in unicity format *file*/*function*, *file*/*class*.*method*
            save : str
                name of file to write docstrings
        '''
        fl,obj,func = split_at_delimiter(routine)
        fp = open(save,'w')
        for cl in self.clientlist:
            fp.write('# {:s}\n'.format(cl.name_email))
            fp.write('if True:\n')
            if fl not in cl.portfolio.files.keys():
                continue
            try:
                if obj is None:
                    ds = cl.portfolio.files[fl].functions[func].docstring
                else:
                    ds = cl.portfolio.files[fl].classes[obj].methods[func].docstring
            except KeyError:
                ds = None
            except AttributeError:
                ds = None
            if ds is not None:
                fp.write('    \'\'\'\n')
                try:
                    fp.write(ds)
                except UnicodeEncodeError:
                    fp.write('WEIRD UNICODE CHARACTERS IN DOCSTRING!')
                fp.write('    \'\'\'\n')
            else:
                fp.write("# no docstring\n")
            fp.write('    pass\n')
        fp.close()
    # similarity methods
    def similarity_report(self, comparison, client = None, save = None):
        ''' Creates a summary of similarity metrics.

            Parameters:
            -----------
            client : str
                Name of client to highlight or 'anon' for anonymised report.
            save : str
                Name of output file (defaults to *client*_*function*.png).

        '''
        # interpret input routine
        fl, obj, func = split_at_delimiter(comparison.routine)
        if func is None:
            func = fl.split('.')[0]
        elif obj is not None:
            func = obj + '.' + func
        
        # set output name
        clientstr = ''
        if client is not None:
            clientstr = client+'_'
        if save is None:
            save = '{:s}similarity_{:s}.png'.format(clientstr, func)
        
        # generate plot
        comparison._plot(self, save, client)
    def compare(self, routine, metric = 'command_freq', ncpus = 1, template = None):
        ''' Compares pairs of portfolios for similarity between implemented Python routine.

            Parameters:
            -----------
            routine : str
                Callable sequence in unicity format for comparison at three levels: {file}, 
                {file}/{function} or {file}/{class}.{method}.
            metric : str, callable
                Distance metric for determining similarity. See below for more information on
                the different metrics available. Users can pass their own metric functions but
                these must adhere to the specification below.
            ncpus : int
                Number of CPUs to use when running comparisons.
            template : str (optional)
                File path to Python template file for referencing the comparison.
            
            Returns:
            --------
            c : unicity.Comparison
                Object containing comparison information.
            Notes:
            ------
            A template file is specified when Python files are likely to exhibit similarity
            due to portfolios developed from a common template. Each portfolio is compared 
            to the template for similarity, and this is 'subtracted' from any similarity between
            a pair of portfolios.

            Exercise caution when drawing conclusions of similarity between short code snippets as
            this increases the likelihood of raising false positives.

            Distance metrics:
            -----------------
            command_freq (default) : Compares the frequency of distinct commands in two scripts. 
                Commands counted include all callables (function/methods), control statements 
                (if/elif/else), looping statements (for/while/continue/break), boolean operators 
                (and/or/not) and try/except. 

            User-defined distance metrics:
            ------------------------------
            User can pass their own callable that computes a distance metric between two files. The
            specification for this callable is
            
                Parameters:
                ~~~~~~~~~~~
                file1 : File
                    Python File object for client 1.
                file2 : File
                    Python File object for client 2.
                template : File
                    Python File object for template file.
                name : str
                    Routine name for comparison. If none, comparison operates on entire file.

                Returns:
                ~~~~~~~~
                dist : float
                    Float between 0 and 1 indicating degree of similarity (0 = highly similar,
                    1 = highly dissimilar).

            User metrics that raise exceptions are caught and passed, with the error message written
            to unicity_compare_errors.txt for debugging.

        '''
        # check comparison metric available
        if not callable(metric):
            assert metric in builtin_compare_routines, "Unrecognized metric \'{:s}\'".format(metric)

        # load template file
        if template is not None:
            assert os.path.isfile(template), 'cannot find template file {:s}'.format(template)
            template = PythonFile(template, zipfile=None)

        # create comparison pairs
        n = len(self.clientlist)
        pairs = [[[i*1,j*1] for j in range(i+1,n)] for i in range(n)]
        pairs = list(chain(*pairs))

        # empty comparison matrix 
        c = Comparison()
        c.matrix = np.zeros((n,n))
        if callable(metric):
            c.metric = 'user_metric_'+metric.__name__
        else:
            c.metric = metric
        c.routine = routine

        # determine function type and eligibility
        fl, obj, func = split_at_delimiter(routine)
        if obj is not None:
            funcname = obj + '.' + func
        else:
            funcname = func
        for cl in self.clientlist:
            try:
                cl.portfolio.files[fl]
            except KeyError:
                # missing file, add a missing tree as a placeholder
                cl.portfolio.files.update({fl:FunctionInfo(tree=-1)})

            # dissociate zipfile for parallel computation
            cl.portfolio.files[fl]._projzip = None

        # jobs to run
        fls1 = [self.clientlist[i].portfolio.files[fl] for i,j in pairs]
        fls2 = [self.clientlist[j].portfolio.files[fl] for i,j in pairs]
        funcs = [funcname]*len(fls1)
        fls0 = [template]*len(fls1)
        pars = zip(fls1,fls2,funcs,fls0)

        # run comparisons
            # choose mapping function: serial vs. parallel
        if ncpus == 1:
            mapper = starmap
        else:
            p = Pool(ncpus)
            mapper = p.starmap
        
        # run comparisons
        if callable(metric):
            compare_routine = metric
        else:
            compare_routine = builtin_compare_routines[metric]

        outs = mapper(partial(compare, compare_routine=compare_routine), pars)

        # unpack results
        notfile = True
        for pair, out in zip(pairs, outs):
            i,j = pair
            # save compare errors
            if type(out) is str:
                if notfile:
                    fp = open('unicity_compare_errors.txt','w')
                    notfile = False
                nm1 = self.clientlist[i].name
                nm2 = self.clientlist[j].name
                fp.write('error comparing {:s} to {:s} using {:s}'.format(nm1,nm2,c.metric))
                fp.write(out)
                out = 4
            c.matrix[i,j] = out
        if not notfile:
            fp.close()
        # restore zipfile buffers
        for cl in self.clientlist:
            try:
                cl.portfolio.files[fl]._projzip = zipfile.ZipFile(cl.portfolio.files[fl]._projzip)
            except AttributeError:
                pass

        return c
    # testing methods\
    def test(self, routine, ncpus = 1, language='python', client=None, timeout = None, **kwargs):
        ''' Runs test suite for function name.

            Parameters:
            -----------
            routine : str
                Callable sequence in unicity format for comparison at three levels: {file}, 
                {file}/{function} or {file}/{class}.{method}.
            ncpus : int
                Number of CPUs to use when running comparisons.
            client : str
                Run test for individual client, writing their code out to file.
            timeout : float
                Only use timeout if you think there is the possiblity of infinite loops.
                Using a timeout will impact performance. Timeout only implemented for serial.
            language : python
                Type of test to run. Base class supports 'python' only. Additional tests can
                be added by subclassing and defining method _test_{language}.

            Notes
            -----
            Comparisons work by running unit test functions defined inside of test_suite.py.
            
            Unit tests for functions should be named test_{function} and for methods
            test_{class}_{method} and must be lower case.

            Unit test should return True if the function passes.

            Subclassed method _test_{language} must take inputs: routine, ncpus, client, timeout and
            **kwargs. Inspect structure of Project._test_python for more details on implementation 
            requirements.
        '''
        # check if test_suite.py exists
        wd = os.getcwd()
        self._tsfile = wd+os.sep+'test_suite.py'
        assert os.path.isfile(self._tsfile), 'no file \'test_suite.py\' to run'
        assert client is None or client in self.client.keys(), 'no such client \'{}\''.format(client)
        assert not (ncpus > 1 and timeout is not None), 'timeout only implemented for serial (ncpus=1)'

        self.__getattribute__('_test_{:s}'.format(language))(routine, ncpus, client, timeout, **kwargs)
        self._run_test = True
    def _routine_availability(self, client, routine):
        ''' check if flags should be returned indicating routine cannot be tested
        '''
        fl,obj,func = split_at_delimiter(routine)

        # file not submitted
        if fl not in client.portfolio.files.keys():
            return -1

        # routine not present
        fnfli = client.portfolio.files[fl]
        
        # syntax errors in ast
        if fnfli.tree == -1:
            return -3

        if obj is not None:
            if obj not in fnfli.classes.keys():
                # method not present
                return -2
        else:
            if func not in fnfli.functions.keys():
                # function not present
                return -2
        
        # no reason to not run test
        return 0
    def _test_python(self, routine, ncpus, client, timeout):
        ''' Test suite for Python files.
        '''
        
        # PREPARE for tests
        # parse test_suite and check if unit test exists
        fl,obj,func = split_at_delimiter(routine)
        ts = PythonFile(self._tsfile, None)
        if obj is None:
            ftest = 'test_'+func
        else:
            ftest = 'test_'+obj+'_'+func
        #ftest = ftest.lower()
        if ftest not in ts.functions.keys():
            raise ValueError('no unit test \'{:s}\' in \'test_suite.py\''.format(ftest))

        # code lines for unit test
        utlns = []
        # user classes called by unit test
        for uclass in ts.functions[ftest].user_classes:
            mthds = ts.classes[uclass].methods.values()
            if len(mthds) == 0:
                utlns += ts.classes[uclass].ln
            else:
                utlns += [ts.classes[uclass].ln[0],]
                for mthd in mthds:
                    utlns += mthd.lns
        # user functions called by unit test
        for uf in ts.functions[ftest].user_funcs:
            utlns.extend(ts.functions[uf].lns)
        # unit test
        utlns.extend(ts.functions[ftest].lns)

        # CONSTRUCT tests
        pars = []
        if client is None:
            cls_ = self.clientlist
        else:
            cls_ = [self.client[client]]
        for cl in cls_:
            # check special cases preventing a test being run
            availability = self._routine_availability(cl, routine)
            if availability != 0:
                pars.append(availability)
                continue

            # construct testing code
            clns = _get_client_code(cl, routine)

            # unit test call
            # (note: try/finally to counter directory changes coded by clients)
            lns = ['#{:s}\n'.format(cl.name)] + clns + utlns
            lns.append('try:')
            lns.append('    from os import getcwd,chdir')
            lns.append('    cwd = getcwd()')
            lns.append('    {:s}()'.format(ftest))
            lns.append('finally:')
            lns.append('    chdir(cwd)')
            pars.append([ln.replace('\t','    ').rstrip()+'\n' for ln in lns])
        

        # RUN tests
        if client is None:
            # running tests for entire cohort
            errs = _run_tests(ncpus, pars, timeout)
        else:
            # running test for just one client
            # run test 
            #err = _run_test(1, pars[0], None)
            err = _run_tests(1, pars, timeout)[0]
            
            # debug - write test to file with err as docstring
            fl = 'test_{:s}_{:s}.py'.format(client, ftest)
            _save_test(fl, err, pars[0])
            return

        # PARSE test output
        # write output as verbatim function with error traceback as docstring
        fail_file = self._get_file_name('fail', subtype=func)
        errs = list(errs)
        # if no errors to report, return
        if not any([e != '' and type(e) is str for e in errs]): 
            return
        if obj is not None:
            func = obj + '.' + func
        # error file
        err_dir = 'failed_{:}'.format(func)
        if not os.path.isdir(err_dir):
            os.makedirs(err_dir)

        for err, cl, lns in zip(errs, self.clientlist, pars):
            # characterise status
            if type(err) is int:
                # test suite did not run (various reasons)
                cl.failed_test_suite = err
                fp = open(err_dir+os.sep+'test_{:s}_{:s}.py'.format(cl.name, ftest),'w')
                fp.write('failure code {:d}: '.format(err))
                if err == -1:
                    fp.write('no file')
                elif err == -2:
                    fp.write('no function/method')
                elif err == -3:
                    fp.write('syntax errors')
                elif err == -4:
                    fp.write('timeout when running code')
                else:
                    raise 'failure code not recognised'
                fp.close()
                continue
            elif err == '':
                # test suite passed - do not modify failure flag, unless not already defined
                try:
                    cl.failed_test_suite
                except AttributeError:
                    cl.failed_test_suite = 0
                continue
            # test suite failed, write function and traceback in docstring
            cl.failed_test_suite = True

            # write fail file
            fl = err_dir+os.sep+'test_{:s}_{:s}.py'.format(cl.name, ftest)
            _save_test(fl, err, lns)
class FunctionVisitor(ast.NodeVisitor):
    ''' Class to gather data on Python file.
    '''
    def __init__(self):
        self.funcs = []
        self.methods = []
        self.names = []
        self.defs = {}
        self.classes = {}
        self.import_lines = []
        self.all_calls = []
        self.in_class = None
        self.reserved = {'for':0,'while':0,'if':0,'else':0,'and':0,
        'break':0,'continue':0,'or':0,'not':0,'tryexcept':0}
    def visit_Call(self,node):
        ''' Save callable name on visit to callable.
        '''
        try:
            self.funcs.append(node.func.id)
            self.all_calls.append(node.func.id)
        except AttributeError:
            self.methods.append(node.func.attr)
            self.all_calls.append(node.func.attr)
        self.generic_visit(node)
    def visit_For(self,node):
        ''' Save use of For loop.
        '''
        self.reserved['for'] += 1
        self.generic_visit(node)
    def visit_While(self,node):
        ''' Save use of While loop.
        '''
        self.reserved['while'] += 1
        self.generic_visit(node)
    def visit_If(self,node):
        ''' Save use of If conditional.
        '''
        self.reserved['if'] += 1
        if len(node.orelse) > 0:
            self.reserved['else'] += 1
        self.generic_visit(node)
    def visit_And(self,node):
        ''' Save use of And bool operator.
        '''
        self.reserved['and'] += 1
        self.generic_visit(node)
    def visit_Or(self,node):
        ''' Save use of Or bool operator.
        '''
        self.reserved['or'] += 1
        self.generic_visit(node)
    def visit_Not(self,node):
        ''' Save use of Not bool operator.
        '''
        self.reserved['not'] += 1
        self.generic_visit(node)
    def visit_Break(self,node):
        ''' Save use of Break.
        '''
        self.reserved['break'] += 1
        self.generic_visit(node)
    def visit_Continue(self,node):
        ''' Save use of Continue.
        '''
        self.reserved['continue'] += 1
        self.generic_visit(node)
    def visit_TryExcept(self,node):
        ''' Save use of Try/Except.
        '''
        self.reserved['tryexcept'] += 1
        self.generic_visit(node)
    def visit_Name(self, node):
        ''' Got to track these in case of visit to Error.
        '''
        self.names.append(node.id)
        self.generic_visit(node)
    def visit_ClassDef(self,node):
        ''' Switches flag to indicate visit is within class definition.
        '''
        cl = ClassInfo() 
        cl.name = node.name
        try:
            cl.base = node.bases[0].id
        except IndexError:
            cl.base = "classic class"
        if type(node.body[0]) is ast.Expr:
            try:
                cl.docstring = node.body[0].value.s           # docstring
            except AttributeError:
                cl.docstring = None
        else:
            cl.docstring = None
        cl.lineno = [node.lineno-1]
        self.classes.update({cl.name:cl})
        self.in_class = node.name
        try:
            self.base_obj = node.bases[0].id
        except IndexError:
            self.base_obj = "classic class"
        self.generic_visit(node)
        self.classes[cl.name].lineno.append(self.lineno)
        self.in_class = None
    def visit_FunctionDef(self,node):
        ''' Save function information on visit to function definition.
        '''
        func = FunctionInfo()                               
        func.name = node.name                               # name
        if self.in_class is not None:
            self.classes[self.in_class].defs.append(node.name)
        func.lineno = [node.lineno-1]                       # first line
        if type(node.body[0]) is ast.Expr:
            try:
                func.docstring = node.body[0].value.s           # docstring
            except AttributeError:
                func.docstring = None
        else:
            func.docstring = None
        self.funcs = []
        self.methods = []
        self.names = []
        self.generic_visit(node)                            # 'visit' the definition
        func.names = self.names
        func.funcs = self.funcs                             # function calls
        func.methods = self.methods                         # method calls
        func.lineno.append(self.lineno)                     # final line
        if self.in_class is not None:
            funcname = self.in_class + '.' + func.name
        else:
            funcname = func.name
        self.defs.update({funcname: func})                 # save definition
    def visit_ImportFrom(self, node):
        ''' Save line number of import statements.
        '''
        self.import_lines.append(node.lineno-1)
    def visit_Import(self, node):
        ''' Save line number of import statements.
        '''
        self.import_lines.append(node.lineno-1)
    def generic_visit(self, node):
        ''' Save line number on generic visit.
        '''
        try:
            self.lineno=node.lineno
        except AttributeError:
            pass
        ast.NodeVisitor.generic_visit(self, node)
class FunctionInfo(object):
    ''' Class to collect function metadata.
    '''
    def __init__(self, **kwargs):
        for k in kwargs.keys():
            self.__setattr__(k, kwargs[k])
    def __repr__(self):
        try:
            return self.name
        except AttributeError:
            return 'FunctionInfoObj'
class ClassInfo(object):
    ''' Class to collect class metadata.
    '''
    def __init__(self, **kwargs):
        self.defs = []
        self.methods = {}
        for k in kwargs.keys():
            self.__setattr__(k, kwargs[k])
    def __repr__(self):
        try:
            return self.name
        except AttributeError:
            return 'ClassInfoObj'
class BaseFile(object):
    ''' Class for generic file.
    '''
    def __init__(self, filename, projzip):
        self.filename = filename
        self._projzip = projzip
        if filename is not None:
            self.load_file()
    def __repr__(self):
        return self.filename
    def load_file(self):
        ''' Load file contents as list of strings.
        '''
        # open file
        if self._projzip is not None:
            fp = self._projzip.open(self.filename,'r')
        else:
            fp = open(self.filename,'r', errors='replace')
        # parse contents
        lns = fp.readlines()
        try:
            self.lns = [ln.decode('utf-8','backslashreplace') for ln in lns]
        except UnicodeDecodeError:
            self.lns = [ln.decode("ISO-8859-1",'backslashreplace') for ln in lns]
        except AttributeError:
            self.lns = [ln for ln in lns]
        fp.close()
    def has_sequence(self, str):
        ''' Checks if file contains specific string sequence.
        '''
        pass
class PNGFile(BaseFile):
    ''' Class to gather data on PNG file.
    '''
    def __init__(self, filename, zipfile):
        super(PNGFile,self).__init__(filename, zipfile)
    def load_file(self):
        ''' Extracts metadata from png file.
        '''
        if self._projzip is not None:
            img = self._projzip.open(self.filename)
            img = Image.open(img)
        else:
            img = Image.open(self.filename)
        for k,v in img.info.items():
            self.__setattr__(k,v)
class TxtFile(BaseFile):
    ''' Class to gather data on txt file.
    '''
    def __init__(self, filename, zipfile):
        super(TxtFile,self).__init__(filename, zipfile)
class CFile(BaseFile):
    ''' Class to gather data on .c source file.
    '''
    def __init__(self, filename, zipfile):
        super(CFile,self).__init__(filename, zipfile)
class PythonFile(BaseFile):
    ''' Class to gather data on Python file.
    '''
    def __init__(self, filename, zipfile):
        super(PythonFile,self).__init__(filename, zipfile)
        self.tree = None
        self.calls = []
        self.parse_file()
    def parse_file(self):
        ''' Parse Python file for function definition info.
        '''
        # load the ast tree
        try:
            self.tree = ast.parse(''.join(self.lns))
        except SyntaxError:
            self.tree = -1
            return
        # visit nodes in the tree
        fv = FunctionVisitor()
        fv.visit(self.tree)
        # save info from tree visit
            # class info
        self.classes = fv.classes
        for k in self.classes.keys():
            ln0,ln1 = self.classes[k].lineno
            self.classes[k].ln = self.lns[ln0:ln1]
            # function info
        self.functions = fv.defs
        for k in self.functions.keys():
            ln0,ln1 = self.functions[k].lineno
            self.functions[k].lns = self.lns[ln0:ln1]
            # link functions to classes
            if '.' in k:
                obj,func = k.split('.')
                self.classes[obj].methods.update({func:self.functions[k]})
        self.import_lines = fv.import_lines
        self.all_calls = fv.all_calls
        self.reserved = fv.reserved
        # post-processing 
        self.get_user_funcs()
        self.get_user_classes()
    def get_user_funcs(self):
        ''' Identify which user defined functions are called from the same file.

            Recurses to identify all dependent functions
        '''
        fks = self.functions.keys()
        for func in self.functions.values():
            # retain only names corresponding to classes
            func.names = [name for name in func.names if name in self.classes.keys()]
            # get user-defined functions directly called
            func.user_funcs = list(set([f for f in func.funcs if f in fks]))

            # recurse, checking if user-defined fuctions call other user-defined functions
            recurseCount = 0
            funcCount = len(func.user_funcs)
            while True:
                # add next recursive level
                for ufunc in func.user_funcs:
                    func.user_funcs += list(set([f for f in self.functions[ufunc].funcs if (f in fks and f not in func.user_funcs)]))

                # test if no additional funcs have been added update func count    
                if len(func.user_funcs) == funcCount:
                    break
                else:
                    funcCount = len(func.user_funcs)

                # update recursion count and check for infinite looping
                recurseCount +=1
                if recurseCount == 100:
                    raise ValueError('uh oh, infinite loop...')
    def get_user_classes(self):
        ''' Identify which user defined classes are called from the same file.

            Recurses to identify all dependent classes
        '''
        clsks = self.classes.keys()
        for fk, func in self.functions.items():
            # get user-defined functions directly called
            if '.' not in fk:
                func.user_classes = list(set([f for f in func.funcs+func.user_funcs if f in clsks]))
            else:
                func.user_classes = []
                obj = fk.split('.')[0]
                if self.classes[obj].base not in ['object','classic class']:
                    func.user_classes.append(self.classes[obj].base)
                for mthd in self.classes[obj].methods:
                    for ufunc in self.functions[obj+'.'+mthd].funcs+self.functions[obj+'.'+mthd].names:
                        if ufunc in clsks and ufunc not in func.user_classes:
                            func.user_classes.append(ufunc)
            # recurse, checking if methods of user-defined classes call other user-defined classes
            recurseCount = 0
            classCount = len(func.user_classes)
            while True:
                # add next recursive level
                for uclass in func.user_classes:
                    for mthd in self.classes[uclass].methods:
                        for ufunc in self.functions[uclass+'.'+mthd].funcs+self.functions[uclass+'.'+mthd].names:
                            if ufunc in clsks and ufunc not in func.user_classes:
                                func.user_classes.append(ufunc)
                    
                # test if no additional funcs have been added update func count    
                if len(func.user_classes) == classCount:
                    break
                else:
                    classCount = len(func.user_classes)

                # update recursion count and check for infinite looping
                recurseCount +=1
                if recurseCount == 100:
                    raise ValueError('uh oh, infinite loop...')
    def get_calls(self, name):
        ''' Return dictionary of callables and their frequency.
        '''
        if name is None:
            all_calls = self.all_calls
        else:
            all_calls = self.functions[name].methods + self.functions[name].funcs
        unique_calls = list(set(all_calls))
        call_dict = dict([(k,0) for k in unique_calls])
        for call in all_calls:
            call_dict[call] = call_dict[call] + 1
        call_dict.update(self.reserved)
        return call_dict

# Exceptions
class ComparisonError(Exception):
    pass

def gev(x,*pars): 
    c,scale = pars
    return c/scale*(x/scale)**(c-1)*np.exp(-(x/scale)**c)
def check_fuzzy_ratio(fl, expect):
    fl, flext = os.path.splitext(fl)
    expect, expect_ext = os.path.splitext(expect)
    if flext.lower() != expect_ext.lower():
        return 0
    else:
        return fuzz.partial_ratio(expect.lower(), fl.lower())
def split_at_delimiter(function):
    if function is None:
        return None, None, None
    if '/' not in function:
        fl = function
        obj = None
        func = None                    
    else:
        fl, func = function.split('/')
        if '.' not in func:
            obj = None
        else:
            obj, func = func.split('.')
    return fl, obj, func        
def _run_tests(ncpus, pars, timeout):
    ''' Logic for queueing and running tests.
    '''
    if ncpus == 1:
        # run tests in serial
        if timeout is None:
            errs = map(_run_test, enumerate(pars))
            return [err for i,err in sorted(errs, key = lambda x: x[0])]
        else:
            manager = Manager()
            errs = manager.dict()
            for i,par in enumerate(pars):
                p = Process(target=_run_test_timeout, args=(i, par, errs))
                p.start()
                p.join(timeout)
                if p.is_alive():
                    print('timeout encountered for {:s}'.format(par[0].rstrip()))
                    p.terminate()
                    errs[i] = -4
                    continue
            return [errs[i] for i in range(len(pars))]
    else:
        # parallel
        p = Pool(ncpus)
        errs = p.map(_run_test, enumerate(pars))
        return [err for i,err in sorted(errs, key = lambda x: x[0])]
def _run_test_timeout(i, lns, errs):
    ''' Runs a Python unit test.
    '''
    # default, no failure
    err = ''
    # no code to run (various reasons)
    if type(lns) is int:
        return lns
    try:
        # run test
        exec(''.join(lns), {})
    except:
        # append traceback info
        err += str(traceback.format_exc())+'\n'
        err += str(sys.exc_info()[0])
    errs[i] = err
def _run_test(lns):
    ''' Runs a Python unit test.
    '''
    # default, no failure
    i,lns = lns
    err = ''
    # no code to run (various reasons)
    if type(lns) is int:
        return [i,lns]
    try:
        # run test
        exec(''.join(lns), {})
    except:
        # append traceback info
        err += str(traceback.format_exc())+'\n'
        err += str(sys.exc_info()[0])
    return (i,err)
def _save_test(fl, err, lns):
    fp = open(fl,'w', encoding='utf-8')
        # error
    fp.write('r\'\'\'\n')
    fp.write(err+'\n')
    fp.write('\'\'\'\n')
        # test
    for ln in lns: 
        fp.write(ln.rstrip()+'\n')
    fp.close()
def repair_filename(fl0, fls):
    ''' Nudge filenames towards expected template (clients can't follow instructions).
    '''
    bestmatch = 3
    repairfl = None
    fle = os.path.splitext(fl0)
    ext = fle[-1]
    fle = fle[0] + ext.lower()

    for fl in fls:
        rt = (1.-SequenceMatcher(None, fle, fl).ratio())*len(fle)
        if rt <= bestmatch:
            bestmatch = rt
            repairfl = copy(fl)

    if repairfl is not None:
        return os.path.splitext(repairfl)[0]+ext.lower()
    else:
        return fl0
def File(filename, zipfile=None):
    ''' Assess file type and return corresponding object.
    '''
    ext = filename.lower().split('.')[-1]

    if zipfile is None:
        assert os.path.isfile(filename), 'cannot find file at location'

    if ext == 'py':
        return PythonFile(filename, zipfile=zipfile)
    elif ext == 'png':
        return PNGFile(filename, zipfile=zipfile)
    elif ext == 'txt':
        return TxtFile(filename, zipfile=zipfile)
    elif ext == 'm':
        return TxtFile(filename, zipfile=zipfile)
    elif ext == 'c':
        return CFile(filename, zipfile=zipfile)
    elif ext == 'md':
        return TxtFile(filename, zipfile=zipfile)
    else:
        raise ValueError('unsupported file extension {:s}'.format(ext))
def compare_command_freq(file1, file2, template, name):
    ''' Compute similarity of two Python callable sets.

        Parameters:
        -----------
        file1 : File
            Python File object for client 1.
        file2 : File
            Python File object for client 2.
        template : File
            Python File object for template file.
        name : str
            Routine name for comparison. If none, comparison operates on entire file.

        Returns:
        --------
        dist : float
            Float between 0 and 1 indicating degree of similarity (0 = highly similar,
            1 = highly dissimilar).

    '''
    # create callable sets
    dict1 = file1.get_calls(name)
    dict2 = file2.get_calls(name)
    # if template available, remove callables in template from sources
    if template is not None:
        dict3 = template.get_calls(name)
        for k in dict3.keys():
            for dict in [dict1, dict2]:
                if k in dict.keys():
                    dict[k] = np.max([0, dict[k]-dict3[k]])
    # compute similarity
    similar = 0
    dissimilar = 0
    for k in list(dict1.keys())+list(dict2.keys()):
        if k in dict1.keys() and k not in dict2.keys():
            dissimilar += dict1[k]
        elif k in dict2.keys() and k not in dict1.keys():
            dissimilar += dict2[k]
        else:
            call_count = [dict1[k], dict2[k]]
            similar += np.min(call_count)
            dissimilar += np.max(call_count) - np.min(call_count)

    if similar+dissimilar < 1:
        dissimilar = 1.

    return 1.-similar/(similar+dissimilar)
def _get_client_code(client, routine):
    '''
    '''
    fl,obj,func = split_at_delimiter(routine)
    fnfli = client.portfolio.files[fl]
    # client's code for running
        # imports 
    clns = [fnfli.lns[iln].lstrip() for iln in fnfli.import_lines]
        # classes
    if obj is not None:
        func = obj + '.' + func
    for uclass in fnfli.functions[func].user_classes:
        mthds = fnfli.classes[uclass].methods.values()
        if len(mthds) == 0:
            clns += fnfli.classes[uclass].ln
        else:
            clns += [fnfli.classes[uclass].ln[0],]
            for mthd in mthds:
                clns += mthd.lns
    if obj is not None:
        clns += [fnfli.classes[obj].ln[0],]
        for mthd in fnfli.classes[obj].methods.values():
            clns += mthd.lns
        # functions
    for uf in fnfli.functions[func].user_funcs:
        clns += fnfli.functions[uf].lns
        # test function
    if obj is None:
        clns += fnfli.functions[func].lns

    return clns
def compare(file1, file2, name, template, compare_routine):
    ''' Compute similarity of two Python functions.
    '''

    # return flags
        # 2 for syntax errors
    if file1.tree == -1 or file2.tree == -1:
        return 2
        # 3 for no file to compare
    if name is not None:
        if name not in file1.functions or name not in file2.functions:
            return 3
    
    # compute pycode_similar score (similarity of ast tree)
    try:
        similarity = compare_routine(file1, file2, template, name)
    except:
        # return flag 4 for unspecified compare errors (set later)
        err = str(traceback.format_exc())+'\n'
        err += str(sys.exc_info()[0])
        return err

    return similarity
def isiterable(x):
    ''' Returns true if input is iterable.
    '''
    try:
        _ = (xi for xi in x)
        return True
    except TypeError:
        return False
builtin_compare_routines = {'command_freq':compare_command_freq}