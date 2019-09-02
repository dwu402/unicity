import os, ast, zipfile, sys, traceback, re, glob, inspect, warnings
import numpy as np
from itertools import starmap
from functools import partial
from copy import copy
from itertools import chain
from multiprocessing import Pool, Process, Manager
from matplotlib import pyplot as plt
import scipy.cluster.hierarchy as sch
from scipy.optimize import curve_fit
from scipy.stats import genextreme
from scipy.spatial.distance import squareform
from PIL import Image
from fnmatch import fnmatch
from difflib import SequenceMatcher
Image.MAX_IMAGE_PIXELS = 1000000000

# silent warning on fuzzywuzzy import
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fuzzywuzzy import fuzz
	
# General classes
class _Cohort(object):
    ''' Class for all clients in a cohort.

        Parameters:
        -----------
        filename : str
            Path to file containing cohort information. 
    '''
    def __init__(self, filename):
        self.filename = filename
        self._load()
    def __repr__(self):
        try:
            return '{:d}cohort'.format(self.year)
        except AttributeError:
            return 'cohort'
    def _load(self):
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

        Attributes:
        -----------
        name : str
            Name associated with client.
        files : dict
            Dictionary of File objects, keyed by file name, associated with the 
            client's portfolio.
        missing : list
            Expected files missing from the client's portfolio.

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
        self.files = {}
        self.missing = []
    def __repr__(self):
        return 'cl:'+self.name
    @property
    def _name_email(self):
        try:
            return '{:s} ({:s})'.format(self.name, self.email)
        except AttributeError:
            return '{:s}'.format(self.name)
class Comparison(object):
    ''' A class for batch comparisons of code.

        Parameters:
        -----------
        loadfile : str
            File path to previously saved comparison object.
        prior_project : unicity.Project (optional)
            If comparison was constructed against a prior project, pass this
            object to read prior client information.

        
        Attributes:
        -----------
        matrix : array-like
            Distance matrix of similarities.
        routine : str
            Code unit for comparison in unicity string format.
        prior_routine : str
            Code unit for prior comparison in unicity string format.

        Methods:
        --------
        save 
            Write comparison data to file.

    '''
    def __init__(self, loadfile, prior_project=None):
        if loadfile is not None:
            self._load(loadfile, prior_project)
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
        allclientlist = proj.clientlist+self._prior_clientlist
        n = len(allclientlist)
        k = 0; Ds = np.zeros(int((n-1)*n/2))
        for i in range(n):
            D[i,i] = 0.
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

        # compute appropriate font size
        ax_inches = 0.6*8.27     # axis dimension in inches
        font_inches = ax_inches/n   # font size in inches
        fs = int(1.2*font_inches*72)  # font size in points
        fs = np.min([fs, 5])
        
        # plotting
        Z1 = sch.dendrogram(Y1, orientation='left', ax=ax1)
        ax1.set_xlim([1.05,0])
        Z2 = sch.dendrogram(Y2, ax=ax2)
        ax2.set_ylim([0,1.05])
        idx1 = Z1['leaves']
        idx2 = Z2['leaves']
        # get client similarity if requested
        if client not in [None, 'anon']:
            ix = [i for i,cl in enumerate(allclientlist) if cl.name == client][0]
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
        try:
            pcut = 0.0
            i = np.argmin(abs(m-pcut))
            scale = np.sum(h[:-1])/np.sum(h[i:-1])
            p = curve_fit(_gev, m[i:-1], h[i:-1]*scale, [0.,0.1],
                bounds = ([0,0],[np.inf,np.inf]))[0]
            x1 = np.linspace(0,1,101)
            axbar.plot(x1, _gev(x1, *p), 'r:', label='best-fit Weibull')
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
            name = allclientlist[idx].name
            col = 'k'
            if client is not None:
                if name != client:
                    name = '*'*np.random.randint(10,15)
                else:
                    col = 'r'
            if idx > len(proj.clientlist):
                col = 'g'
                
            ax1b.text(0.9*x0, (i+0.5)*dy, name, size=fs, color = col, ha='right', va='center')
            if i % dn == 0:
                ax1b.axhline(i*dy, color = 'k', linestyle='-', linewidth=0.25)
                ax1.axhline(i*dy, color = 'k', linestyle='-', linewidth=0.25)

        dx = ax2b.get_xlim()[1]/n
        y0 = ax2b.get_ylim()[0]
        for i,idx in enumerate(Z2['leaves']):
            name = allclientlist[idx].name
            col = 'k'
            if client is not None:
                if name != client:
                    name = '*'*np.random.randint(10,15)
                else:
                    col = 'r'
                    lbl = 'score - {:3.2f}'.format(max_similarity)
                    axbar.axvline(max_similarity,color='r',linestyle = '-', label=lbl)
            if idx > len(proj.clientlist):
                col = 'g'
            axbar.legend()
                
            ax2b.text((i+0.5)*dx, 0.95*y0, name, size=fs, color = col, ha='center', 
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
    def _load(self, loadfile, prior_project):
        ''' Loads a precomputed comparison file.
        '''
        fp = open(loadfile,'r')
        ln = fp.readline().strip().split()
        n = int(ln[0])
        self.routine = ln[1]
        self.metric = ln[2]
        try:
            self.prior_routine = ln[3]
        except IndexError:
            self.prior_routine = None
        fp.close()
        # read matrix
        self.matrix = np.genfromtxt(loadfile, skip_header=1)
        if prior_project is not None:
            self._prior_clientlist = prior_project.clientlist
        else:
            self._prior_clientlist = []
    def save(self, savefile):
        ''' Saves a precomputed comparison file.

            Parameters:
            -----------
            savefile : str
                Name of file to save similarity data.
        '''
        fp = open(savefile,'w')
        n = self.matrix.shape[0]
        # header data
        fp.write('{:d} '.format(n))                                  # number of clients
        fp.write((' {:s} {:s}').format(self.routine, self.metric))
        if self.prior_routine is not None:
            fp.write(' {:s}'.format(self.prior_routine))
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
            Path to file containing information about clients.
        root : str (optional)
            String for naming of output files.
        
        Attributes:
        -----------
        client : dict
            Dictionary of Client objects, keyed by client name.
        clientlist : list
            List of Client objects, ordered alphabetically by client name.
        portfolio_status : dict
            Contains completeness information about individual client portfolios.
        test_status : dict
            Contains testing information about individual client portfolios.
        
        Methods:
        --------
        findstr
            Look for string instances in client portfolios.
        dump_docstrings
            Write docstring information to file.
        compare
            Compute similarity metrics between client portfolios.
        similarity_report
            Produce a plot of similarity across the project.
        summarise
            Output a summary of the project.
        test
            Batch testing of the code.

        Notes:
        ------
        Cohort file should contain client information in CSV format. The first row
        defines column names and must at least contain a 'name' column. Client information
        is given on separate rows.

        Each column is provisioned as a separate attribute for each client as discovered. If the
        'email' attribute is present, this will be reported in output.
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
            self._cohort = _Cohort(cohort)
        else:
            self._cohort = None
        self._parse_filepath()
        self._expecting = expecting
        self._ignore_files = ignore
        self._run_test = False
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        self._parent_script = module.__file__
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
        if max([_check_fuzzy_ratio(fl, ignore) for ignore in self._ignore_files])>75:
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

            # fuzzy string matching because people can't follow instructions
            ratios = [_check_fuzzy_ratio(fl, expect) for expect in self._expecting]

            # accept above (arbitrary) threshold
            if max(ratios)>75:
                fl0 = self._expecting[np.argmax(ratios)]
            else:
                # check against ignore list
                self._ignore(fl)
                continue 

            client.files.update({fl0:_File(fl, zf)})            # save file information
        
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
            
            if self._cohort is not None:
                if name not in self._cohort.name:
                    raise ValueError("client '{}' from file '{}' not in cohort file '{}'".format(
                        name, fl, self._cohort.filename 
                    ))

            cl = Client(name, self._cohort)
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
    def _check_portfolio_status(self):
        ''' Compile portfolio completeness information.
        '''
        # clients with absent portfolios (if cohort info available)
        if self._cohort is not None:
            submitted = self.client.keys()
            self.portfolio_status['absent'] = [Client(name, self._cohort) for name in self._cohort.name if name not in submitted]
        
        # clients with partial portfolios (if expecting defined)
        if self._expecting is None:
            return

        for cl in self.clientlist:
            # partial portfolios (missing files)
            cl.missing = list(set(self._expecting) - set(cl.files.keys()))
            if len(cl.missing) > 0:
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
            elif cl.failed_test_suite == -3:
                # syntax errors in code
                self.test_status['compile error'].append(cl)
            elif cl.failed_test_suite:
                # failed test suite
                self.test_status['failed'].append(cl)
            elif not cl.failed_test_suite:
                # passed test suite
                self.test_status['passed'].append(cl)
    def _split_at_delimiter(self, function, prior_project = None):
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

        # check file exists
        proj = self
        if prior_project is not None:
            proj = prior_project
        if fl not in proj._expecting:
            raise UnicityError("'{:s}' not an expected client file".format(fl))
        
        # check routine exists
        funcname =  obj + '.' + func if obj is not None else func
        if funcname is not None:
            presence = 0.
            for cl in self.clientlist:
                try:
                    cl.files[fl].functions[funcname]
                    presence += 1
                except:
                    pass
            presence = presence/len(self.clientlist)
            if presence < 0.1:
                raise UnicityError("'{:s}' does not appear frequently in '{}'".format(funcname,fl))
        
        return fl, obj, func        
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
        fl,obj,func = self._split_at_delimiter(location)
        if obj is not None:
            func = obj + '.' + func
        if save is not None:
            fp = open(save, 'w')
        # loop over clients in order
        found_clients = []
        for cl in self.clientlist:
            written_name = False
            # extract lines filtered by file or routine
            for fln,fli in cl.files.items():
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
                elif fli._tree == -1:
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
    def summarise(self, save, verbose=False):
        ''' Create log file with portfolio information.

            Parameters:
            -----------
            save : str
                File path to save output summary.
            verbose : bool (optional)
                Print output to screen as well.
        '''
        self._check_test_status()
        # open log file
        fp = open(save, 'w')
        fline = (80*"-")+'\n'

        # header
        fp.write("Portfolio information for {:s}\n".format(self._root))
        fp.write(fline)
        fp.write('\n')

        # high-level, highlighting missing or incomplete portfolios
        fp.write(fline)
        fp.write("SUMMARY\n")
        fp.write(fline)
        if self._cohort is not None:
            fp.write("{:s}: {:d} clients\n".format(self._cohort.filename, len(self._cohort.name)))
        else:
            fp.write("cohort: {:d} clients\n".format(len(self.clientlist)))
        fp.write('-----\n')
        fp.write('{:d} clients with complete portfolios\n'.format(len(self.portfolio_status['complete'])))
        fp.write('{:d} clients with partial portfolios\n'.format(len(self.portfolio_status['partial'])))
        if self._cohort is not None:
            fp.write('{:d} clients with absent portfolio\n'.format(len(self.portfolio_status['absent'])))
        
        if self._run_test:
            fp.write('-----\n')
            fp.write('{:d} clients passed the test suite\n'.format(len(self.test_status['passed'])))
            fp.write('{:d} clients failed the test suite\n'.format(len(self.test_status['failed'])))
            fp.write('{:d} clients had syntax errors (no test run)\n'.format(len(self.test_status['compile error'])))
            fp.write('{:d} clients had no file (no test run)\n'.format(len(self.test_status['missing file'])))
        
        fp.write('\n')

        # more information about incomplete portfolios
        if len(self.portfolio_status['partial']) != 0:
            fp.write(fline)
            fp.write("PARTIAL PORTFOLIOS\n")
            fp.write(fline)
            for cl in self.portfolio_status['partial']:
                fp.write('{:s}, missing '.format(cl._name_email))
                fp.write((len(cl.missing)*'{:s}, ').format(*(cl.missing))[:-2]+'\n')
            fp.write('\n')

        # more information about absent portfolios
        if len(self.portfolio_status['absent']) != 0:
            fp.write(fline)
            fp.write("ABSENT PORTFOLIOS\n")
            fp.write(fline)
            for cl in self.portfolio_status['absent']:
                fp.write('{:s}\n'.format(cl._name_email))
            fp.write('\n')

        # more information about failed tests, syntax errors, absent tests
        reports = [
            ['failed','FAILED TEST SUITE'],
            ['missing file',"FILE NOT INCLUDED IN PORTFOLIO"],
            ['compile error',"SYNTAX ERRORS DURING COMPILE"],
            ]
        for key, msg in reports:
            if len(self.test_status[key]) != 0:
                fp.write(fline)
                fp.write("{:s}\n".format(msg))
                fp.write(fline)
                for cl in self.test_status[key]:
                    fp.write('{:s}\n'.format(cl._name_email))
                fp.write('\n')
        fp.close()

        # optional print to screen
        if verbose:
            with open(save, 'r') as fp:
                lns = fp.readlines()
            
            for ln in lns:
                print(ln.strip())
    def dump_docstrings(self, routine, save):
        ''' Writes docstring information out to file.

            Parameters:
            -----------
            routine : str
                Callable sequence in unicity format {file}/{function}, or
                {file}/{class}.{method}.
            save : str
                File path to write docstrings.
        '''
        fl,obj,func = self._split_at_delimiter(routine)
        fp = open(save,'w')
        for cl in self.clientlist:
            fp.write('# {:s}\n'.format(cl._name_email))
            fp.write('if True:\n')
            if fl not in cl.files.keys():
                continue
            try:
                if obj is None:
                    ds = cl.files[fl].functions[func].docstring
                else:
                    ds = cl.files[fl].classes[obj].methods[func].docstring
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
            comparison : unicity.Comparison
                Comparison object produced by Project.compare.
            client : str (optional)
                Name of client to highlight or 'anon' for anonymised report.
            save : str (optional)
                Name of output file (default to {clientname}_{function}.png).

        '''
        # interpret input routine
        fl, obj, func = self._split_at_delimiter(comparison.routine)
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
    def compare(self, routine, metric = 'command_freq', ncpus = 1, template = None, 
        prior_project = None, prior_routine = None):
        ''' Compares pairs of portfolios for similarity between implemented Python routine.

            Parameters:
            -----------
            routine : str
                Callable sequence in unicity format for comparison at three levels: {file}, 
                {file}/{function} or {file}/{class}.{method}.
            metric : str, callable (optional)
                Distance metric for determining similarity. See below for more information on
                the different metrics available. Users can pass their own metric functions but
                these must adhere to the specification below. (default 'command_freq')
            ncpus : int (optional)
                Number of CPUs to use when running comparisons. (default 1, single thread)
            template : str (optional)
                File path to Python template file for referencing the comparison.
            prior_project : unicity.Project (optional)
                Project object for different cohort. Check current cohort for similarities with 
                previous. Comparisons will not be made between clients of the previous project.
            prior_routine : str (optional)
                Callable sequence in unicity format for comparison from prior_project. If not given,
                will default to routine.

            Returns:
            --------
            c : unicity.Comparison
                Object containing comparison information.

            Notes:
            ------
            A template file is specified when Python files are likely to exhibit similarity
            due to portfolios developed from a common template. Each portfolio is compared 
            to the template for similarity, and this is 'subtracted' from any similarity 
            between a pair of portfolios.

            Exercise caution when drawing conclusions of similarity between short code snippets as
            this increases the likelihood of false positives. 

            Distance metrics:
            -----------------
            command_freq (default) : Compares the frequency of distinct commands in two scripts. 
                Commands counted include all callables (function/methods), control statements 
                (if/elif/else), looping statements (for/while/continue/break), boolean operators 
                (and/or/not) and try/except. 
            jaro : Compares the order of the statements above for matches and transpositions.

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
                name1 : str
                    Routine name in first file for comparison. If not given, the comparison 
                    is assumed to operate on entire file.
                name2 : str
                    Routine name in second file for comparison. If not given, the comparison 
                    is assumed to operate on entire file.

                Returns:
                ~~~~~~~~
                dist : float
                    Float between 0 and 1 indicating degree of similarity (0 = highly similar,
                    1 = highly dissimilar).

            User metrics that raise exceptions are caught and passed, with the error message written
            to unicity_compare_errors.txt for debugging.

            See example/similarity_check.py at https://https://github.com/ddempsey/unicity for more details and examples.
        '''
        # check comparison metric available
        if not callable(metric):
            assert metric in _builtin_compare_routines, "Unrecognized metric \'{:s}\'".format(metric)

        # check prior routine only specified if prior project given
        assert not (prior_routine is not None and prior_project is None), "must pass prior_project if you're going to pass prior_routine"
        if prior_routine is None:
            prior_routine = routine        

        # load template file
        if template is not None:
            assert os.path.isfile(template), 'cannot find template file {:s}'.format(template)
            template = PythonFile(template, zipfile=None)
            if template._tree == -1:
                raise UnicityError("Cannot perform compare due to syntax errors in \'{:s}\' - see below:\n\n{:s}".format(template.filename, template._tree_err))

        # preparation for prior project
        if prior_project is not None:
            prior_clientlist = prior_project.clientlist
        else:
            prior_clientlist = []

        # create comparison pairs
        n1 = len(self.clientlist)
        n2 = len(prior_clientlist)
        # pairs excludes matches between clients in prior list
        pairs = [[[i*1,j*1] for j in range(i+1,n1+n2) if not (i>n1 and j>n1)] for i in range(n1+n2)]
        pairs = list(chain(*pairs))

        # empty comparison matrix 
        c = Comparison(None)
        c.matrix = np.zeros((n1+n2,n1+n2))+4.
        if callable(metric):
            c.metric = 'user_metric_'+metric.__name__
        else:
            c.metric = metric
        c.routine = routine
        c.prior_routine = prior_routine

        # determine function type and eligibility
        fl, obj, func = self._split_at_delimiter(routine)
        fl1, obj1, func1 = self._split_at_delimiter(prior_routine, prior_project)
        
        # get routine name
        funcname =  obj + '.' + func if obj is not None else func
        funcname1 =  obj1 + '.' + func1 if obj1 is not None else func1

        for cl in self.clientlist:
            try:
                cl.files[fl]
            except KeyError:
                # missing file, add a missing tree as a placeholder
                cl.files.update({fl:FunctionInfo(_tree=-1)})

            # dissociate zipfile for parallel computation
            cl.files[fl]._projzip = None

        for cl in prior_clientlist:
            try:
                cl.files[fl1]
            except KeyError:
                # missing file, add a missing tree as a placeholder
                cl.files.update({fl1:FunctionInfo(_tree=-1)})

            # dissociate zipfile for parallel computation
            cl.files[fl1]._projzip = None

        # jobs to run
        allclientlist = self.clientlist + prior_clientlist
        fls1 = [allclientlist[i].files[fl] if i<n1 else allclientlist[i].files[fl1] for i,j in pairs]
        fls2 = [allclientlist[j].files[fl] if j<n1 else allclientlist[j].files[fl1] for i,j in pairs]
        funcs1 = [funcname if i<n1 else funcname1 for i,j in pairs]
        funcs2 = [funcname if j<n1 else funcname1 for i,j in pairs]
        
        fls0 = [template]*len(fls1)
        pars = zip(fls1,fls2,funcs1,funcs2,fls0)

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
            compare_routine = _builtin_compare_routines[metric]

        outs = mapper(partial(_compare, compare_routine=compare_routine), pars)

        # unpack results
        notfile = True
        for pair, out in zip(pairs, outs):
            i,j = pair
            # save compare errors
            if type(out) is str:
                if notfile:
                    fp = open('unicity_compare_errors.txt','w')
                    notfile = False
                nm1 = allclientlist[i].name
                nm2 = allclientlist[j].name
                fp.write('error comparing {:s} to {:s} using {:s}'.format(nm1,nm2,c.metric))
                fp.write(out)
                out = 4
            c.matrix[i,j] = out
        if not notfile:
            fp.close()
        # restore zipfile buffers
        for cl in self.clientlist:
            try:
                cl.files[fl]._projzip = zipfile.ZipFile(cl.files[fl]._projzip)
            except AttributeError:
                pass

        c._prior_clientlist = prior_clientlist
        return c
    # testing methods
    def test(self, routine, ncpus = 1, language='python', client=None, timeout = None, 
        **kwargs):
        ''' Runs test suite for function name.

            Parameters:
            -----------
            routine : str
                Name of unit test function (not a function handle).
            ncpus : int (optional)
                Number of CPUs to use when running comparisons. (default 1, single thread)
            client : str (optional)
                Run test for individual client, writing their code out to file. (default is to run
                test for all clients.)
            timeout : float (optional)
                Time after which test should be exited. Only use timeout if you think there 
                is the possiblity of infinite loops. Using a timeout will impact performance. 
                Timeout only implemented for serial. (default is no timeout)
            language : python
                Type of test to run. Base class supports 'python' only. Additional tests can
                be added by subclassing and defining new method _test_{language}.
            **kwargs 
                Passed to language specific method _test_{language}

            Notes
            -----
            Testing proceeds by running a unit test function defined within the script from
            which the test method is called.

            The unit test should contain at least one import statement to the generically
            named client file (the file name passed to 'expecting' when constructing the Project.)
            
            The unit test should raise an error if the client's code is in error. For instance
            an assert statement can be used to check a result is returned correctly.

            See example/batch_testing.py at https://https://github.com/ddempsey/unicity for more details and examples.
        '''
        # check if test_suite.py exists
        wd = os.getcwd()
        self._tsfile = self._parent_script
        assert client is None or client in self.client.keys(), 'no such client \'{}\''.format(client)
        assert not (ncpus > 1 and timeout is not None), 'timeout only implemented for serial (ncpus=1)'

        self.__getattribute__('_test_{:s}'.format(language))(routine, ncpus, client, timeout, **kwargs)
        self._run_test = True
    def _test_python(self, routine, ncpus, client, timeout):
        ''' Test suite for Python files.
        '''
        
        # PREPARE for tests
        # parse test_suite and check if unit test exists
        ts = PythonFile(self._tsfile, None)
        
        # code lines for unit test
        utlns = []
        # user classes called by unit test
        for uclass in ts.functions[routine].user_classes:
            mthds = ts.classes[uclass].methods.values()
            if len(mthds) == 0:
                utlns += ts.classes[uclass].ln
            else:
                utlns += [ts.classes[uclass].ln[0],]
                for mthd in mthds:
                    utlns += mthd.lns
        # user functions called by unit test
        for uf in ts.functions[routine].user_funcs:
            utlns.extend(ts.functions[uf].lns)
        # unit test - remove import_froms calling out to test file
        lns = []
        found_client_file_import = False
        for ln in ts.functions[routine].lns:
            if 'from ' in ln and ' import ' in ln:
                if ln.split('from ')[1].split(' import')[0].strip()+'.py' in self._expecting:
                    found_client_file_import = True
                    continue
            lns.append(ln)
        utlns.extend(lns)

        # check for misspellings
        if not found_client_file_import:
            raise UnicityError("test function '{:s}' does not contain import statements to client files".format(routine))

        # CONSTRUCT tests
        pars = []
        if client is None:
            cls_ = self.clientlist
        else:
            cls_ = [self.client[client]]
        for cl in cls_:

            # construct testing code
            clns = _get_client_code(cl, ts.functions[routine].import_froms)

            # catch errors
            if type(clns) == int:
                pars.append(clns)
                continue

            # unit test call
            # (note: try/finally to counter directory changes coded by clients)
            lns = ['#{:s}\n'.format(cl.name)] + clns + utlns
            lns.append('try:')
            lns.append('    from os import getcwd,chdir')
            lns.append('    cwd = getcwd()')
            lns.append('    {:s}()'.format(routine))
            lns.append('finally:')
            lns.append('    chdir(cwd)')
            pars.append([ln.replace('\t','    ').rstrip()+'\n' for ln in lns])
        
        # error file
        err_dir = 'failed_{:}'.format(routine)
        if not os.path.isdir(err_dir):
            os.makedirs(err_dir)

        # RUN tests
        if client is None:
            # running tests for entire cohort
            errs = _run_tests(ncpus, pars, timeout)
        else:
            # running test for just one client
            err = _run_tests(1, pars, timeout)[0]
            
            # debug - write test to file with err as docstring
            fl = err_dir+os.sep+'test_{:s}_{:s}.py'.format(cl.name, routine)
            _save_test(fl, err, pars[0])
            return

        # PARSE test output
        # write output as verbatim function with error traceback as docstring
        fail_file = self._get_file_name('fail', subtype=routine)
        errs = list(errs)
        
        # if no errors to report, return
        if not any([e != '' for e in errs]): 
            return

        for err, cl, lns in zip(errs, self.clientlist, pars):
            # characterise status
            if type(err) is int:
                # test suite did not run (various reasons)
                cl.failed_test_suite = err
                _save_test(err_dir+os.sep+'test_{:s}_{:s}.py'.format(cl.name, routine), err, lns, cl)
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
            fl = err_dir+os.sep+'test_{:s}_{:s}.py'.format(cl.name, routine)
            _save_test(fl, err, lns)
class _FunctionVisitor(ast.NodeVisitor):
    ''' Class to gather data on Python file.
    '''
    def __init__(self):
        self.funcs = []
        self.methods = []
        self.names = []
        self.defs = {}
        self.classes = {}
        self.import_lines = []
        self.import_froms = []
        self.function_import_froms = []
        self.all_calls = []
        self.all_keywords = []
        self.in_class = None
        self.reserved = {'for':0,'while':0,'if':0,'else':0,'and':0,
        'break':0,'continue':0,'or':0,'not':0,'tryexcept':0,'import':0,
        'import_from':0}
    def visit_Call(self,node):
        ''' Save callable name on visit to callable.
        '''
        try:
            self.funcs.append(node.func.id)
            self.all_calls.append(node.func.id)
            self.all_keywords.append(node.func.id)
        except AttributeError:
            self.methods.append(node.func.attr)
            self.all_calls.append(node.func.attr)
            self.all_keywords.append(node.func.attr)
        self.generic_visit(node)
    def visit_For(self,node):
        ''' Save use of For loop.
        '''
        self.reserved['for'] += 1
        self.all_keywords.append('for')
        self.generic_visit(node)
    def visit_While(self,node):
        ''' Save use of While loop.
        '''
        self.reserved['while'] += 1
        self.all_keywords.append('while')
        self.generic_visit(node)
    def visit_If(self,node):
        ''' Save use of If conditional.
        '''
        self.reserved['if'] += 1
        self.all_keywords.append('if')
        if len(node.orelse) > 0:
            self.reserved['else'] += 1
            self.all_keywords.append('else')
        self.generic_visit(node)
    def visit_And(self,node):
        ''' Save use of And bool operator.
        '''
        self.reserved['and'] += 1
        self.all_keywords.append('and')
        self.generic_visit(node)
    def visit_Or(self,node):
        ''' Save use of Or bool operator.
        '''
        self.reserved['or'] += 1
        self.all_keywords.append('or')
        self.generic_visit(node)
    def visit_Not(self,node):
        ''' Save use of Not bool operator.
        '''
        self.reserved['not'] += 1
        self.all_keywords.append('not')
        self.generic_visit(node)
    def visit_Break(self,node):
        ''' Save use of Break.
        '''
        self.reserved['break'] += 1
        self.all_keywords.append('break')
        self.generic_visit(node)
    def visit_Continue(self,node):
        ''' Save use of Continue.
        '''
        self.reserved['continue'] += 1
        self.all_keywords.append('continue')
        self.generic_visit(node)
    def visit_TryExcept(self,node):
        ''' Save use of Try/Except.
        '''
        self.reserved['tryexcept'] += 1
        self.all_keywords.append('tryexcept')
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
        n_keywords = len(self.all_keywords)
        self.generic_visit(node)
        self.classes[cl.name].all_keywords = self.all_keywords[n_keywords:]
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
        self.function_import_froms = []
        n_keywords = len(self.all_keywords)
        self.generic_visit(node)                            # 'visit' the definition
        func.names = self.names
        func.all_keywords = self.all_keywords[n_keywords:]
        func.funcs = self.funcs                             # function calls
        func.methods = self.methods                         # method calls
        func.import_froms = self.function_import_froms
        func.lineno.append(self.lineno)                     # final line
        if self.in_class is not None:
            funcname = self.in_class + '.' + func.name
        else:
            funcname = func.name
        self.defs.update({funcname: func})                 # save definition
    def visit_ImportFrom(self, node):
        ''' Save line number of import statements.
        '''
        self.reserved['import_from'] += 1
        self.all_keywords.append('import_from')
        self.import_lines.append(node.lineno-1)
        for name in node.names:
            self.import_froms.append([node.module, name.name])
            self.function_import_froms.append([node.module, name.name])
    def visit_Import(self, node):
        ''' Save line number of import statements.
        '''
        self.reserved['import'] += 1
        self.all_keywords.append('import')
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
    ''' Class containing information about Python callable.

        Attributes:
        -----------
        all_keywords : list
            All callables and reserved keywords in file, in order of appearance.
        docstring : str
            Docstring for the function.
        funcs : list
            Names of functions called within this function.
        import_froms : list
            List of [module, thing] import from statements in from {module} import {thing} format.
        lineno : list
            First and last line number of function in file.
        lns : list
            Text of function.
        methods : list
            Names of methods called within the function.
        name : str
            Name of the funtion.
        names : list
            A python ast category I don't fully understand but useful for catching when
            the client invokes an Exception.
        user_classes : list
            Names of classes defined by the client and used within this function.
        user_funcs : list
            Names of functions defined by the client and used within this funcion.
        
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
    ''' Class containing information about Python class.

        Attributes:
        -----------
        all_keywords : list
            All callables and reserved keywords in file, in order of appearance.
        base : str
            Base class.
        defs : list
            Names of methods defined within the class.
        docstring : string
            Docstring for the class.
        lineno: list
            First and last line number of class definition in file.
        lns : list
            Text of class.
        methods : list
            Names of methods called within the class.
        name : str
            Name of the class.
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
    ''' Class containing information about Python file.

        Attributes:
        -----------
        all_calls : list
            All callables in file, in order of appearance.
        all_keywords : list
            All callables and reserved keywords in file, in order of appearance.
        classes : dict
            ClassInfo objects corresponding to classes defined in file.
        filename : str
            Name of file.
        functions : dict
            FunctionInfo objects corresponding to callables defined in file.
        import_froms : list
            List of [module, thing] import from statements in from {module} import {thing} format.
        import_lines : list
            Line numbers of import statements.
        lns : list
            Text of file.
        reserved : dict
            Frequency of reserved keywords.
    '''
    def __init__(self, filename, zipfile):
        super(PythonFile,self).__init__(filename, zipfile)
        self._tree = None
        self._parse_file()
    def _parse_file(self):
        ''' Parse Python file for function definition info.
        '''
        # load the ast tree
        try:
            self._tree = ast.parse(''.join(self.lns))
            self._tree_err = ''
        except SyntaxError:
            self._tree = -1
            self._tree_err = ''
            self._tree_err += str(traceback.format_exc())+'\n'
            self._tree_err += str(sys.exc_info()[0])
            return
        # visit nodes in the tree
        fv = _FunctionVisitor()
        fv.visit(self._tree)
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
        self.import_froms = fv.import_froms
        self.all_calls = fv.all_calls
        self.all_keywords = fv.all_keywords
        self.reserved = fv.reserved
        # post-processing 
        self._get_user_funcs()
        self._get_user_classes()
    def _get_user_funcs(self):
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
    def _get_user_classes(self):
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
                    if uclass not in self.classes.keys(): continue
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
    def _get_calls(self, name):
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
class UnicityError(Exception):
    pass

def _gev(x,*pars): 
    c,scale = pars
    return c/scale*(x/scale)**(c-1)*np.exp(-(x/scale)**c)
def _check_fuzzy_ratio(fl, expect):
    fl, flext = os.path.splitext(fl)
    expect, expect_ext = os.path.splitext(expect)
    if flext.lower() != expect_ext.lower():
        return 0
    else:
        return fuzz.partial_ratio(expect.lower(), fl.lower())
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
def _save_test(fl, err, lns, cl = None):
    if type(err) is int:
        # test suite did not run (various reasons)
        fp = open(fl,'w')
        fp.write('failure code {:d}: '.format(err))
        if err == -1:
            fp.write('no file')
        elif err == -3:
            fp.write('syntax errors')
            for fli in cl.files.values():
                if fli._tree == -1:
                    fp.write('\n\n{:s}'.format(fli._tree_err))
        elif err == -4:
            fp.write('timeout when running code')
        else:
            raise 'failure code not recognised'
        fp.close()
        return
    elif err == '':
        return

    fp = open(fl,'w', encoding='utf-8')
        # error
    fp.write('r\'\'\'\n')
    fp.write(err+'\n')
    fp.write('\'\'\'\n')
        # test
    for ln in lns: 
        fp.write(ln.rstrip()+'\n')
    fp.close()
def _File(filename, zipfile=None):
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
def _compare_command_freq(file1, file2, template, name1, name2):
    ''' Compute similarity of two Python callable sets.

        Parameters:
        -----------
        file1 : File
            Python File object for client 1.
        file2 : File
            Python File object for client 2.
        template : File
            Python File object for template file.
        name1 : str
            Routine name for comparison (file1). If none, comparison operates on entire file.
        name2 : str
            Routine name for comparison (file2). If none, comparison operates on entire file.

        Returns:
        --------
        dist : float
            Float between 0 and 1 indicating degree of similarity (0 = highly similar,
            1 = highly dissimilar).

    '''
    # create callable sets
    dict1 = file1._get_calls(name1)
    dict2 = file2._get_calls(name2)
    # if template available, remove callables in template from sources
    if template is not None:
        dict3 = template._get_calls(name1)
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
def _jaro(s, t):
    '''Jaro distance between two strings.
    
        Implementation from https://rosettacode.org/wiki/Jaro_distance#Python
    '''
    s_len = len(s)
    t_len = len(t)
 
    if s_len == 0 and t_len == 0:
        return 1
 
    match_distance = (max(s_len, t_len) // 2) - 1
 
    s_matches = [False] * s_len
    t_matches = [False] * t_len
 
    matches = 0
    transpositions = 0
 
    for i in range(s_len):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, t_len)
 
        for j in range(start, end):
            if t_matches[j]:
                continue
            if s[i] != t[j]:
                continue
            s_matches[i] = True
            t_matches[j] = True
            matches += 1
            break
 
    if matches == 0:
        return 0
 
    k = 0
    for i in range(s_len):
        if not s_matches[i]:
            continue
        while not t_matches[k]:
            k += 1
        if s[i] != t[k]:
            transpositions += 1
        k += 1
 
    return ((matches / s_len) +
            (matches / t_len) +
            ((matches - transpositions / 2) / matches)) / 3
def _compare_jaro(file1, file2, template, name1, name2):
    ''' Compute similarity of two Python callable sets based on Jaro distance.

        Parameters:
        -----------
        file1 : File
            Python File object for client 1.
        file2 : File
            Python File object for client 2.
        template : File
            Python File object for template file.
        name1 : str
            Routine name for comparison (file1). If none, comparison operates on entire file.
        name2 : str
            Routine name for comparison (file2). If none, comparison operates on entire file.

        Returns:
        --------
        dist : float
            Float between 0 and 1 indicating degree of similarity (0 = highly similar,
            1 = highly dissimilar).
    '''
    # convert ordered callable set to string
    if name1 is None:
        all_keywords1 = file1.all_keywords
        all_keywords2 = file2.all_keywords
        if template is not None:
            all_keywords0 = template.all_keywords
    else:
        all_keywords1 = file1.functions[name1].all_keywords
        all_keywords2 = file2.functions[name2].all_keywords
        if template is not None:
            all_keywords0 = template.functions[name1].all_keywords
        
    # remove template content if given
    if template is not None:
        for kw0 in all_keywords0:
            try:
                all_keywords1.remove(kw0)
            except ValueError:
                pass
            try:
                all_keywords2.remove(kw0)
            except ValueError:
                pass

    # compute similarity
    similar = _jaro(all_keywords1, all_keywords2)
    
    return 1.-similar
def _get_client_code(client, import_froms):
    '''
    '''
    ilns = []
    clns = []
    included_files = []
    
    for import_from in import_froms:
        fl,item = import_from
        # import not client code, write out verbatim
        if fl+'.py' not in client.files.keys():
            ilns.append('from {:s} import {:s}'.format(fl, item))
            continue

        if fl+'.py' in included_files:
            continue
        else:
            included_files.append(fl+'.py')

        # import is a custom, gather client code
        fnfli = client.files[fl+'.py']
        if fnfli._tree == -1:
            return -3
        clns += fnfli.lns
        
    # client file not found, return empty
    if len(included_files) == 0:
        return -1
    else:
        return ilns+clns
def _compare(file1, file2, name1, name2, template, compare_routine):
    ''' Compute similarity of two Python functions.
    '''

    # return flags
        # 2 for syntax errors
    if file1._tree == -1 or file2._tree == -1:
        return 2
        # 3 for no file to compare
    if name1 is not None:
        if name1 not in file1.functions or name2 not in file2.functions:
            return 3
    
    # compute pycode_similar score (similarity of ast tree)
    try:
        similarity = compare_routine(file1, file2, template, name1, name2)
    except:
        # return flag 4 for unspecified compare errors (set later)
        err = str(traceback.format_exc())+'\n'
        err += str(sys.exc_info()[0])
        return err

    return similarity

_builtin_compare_routines = {'command_freq':_compare_command_freq,'jaro':_compare_jaro}