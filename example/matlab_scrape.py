from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import numpy as np
import openpyxl

fns,hrefs = np.genfromtxt('scraped.csv',delimiter=',',usecols=(0,1),dtype='unicode').T
'''
wb = openpyxl.load_workbook('scraped.xlsx')
ws = wb['scraped']

hrefs = []
for i,fn in enumerate(fns):
    hrefs.append(ws.cell(row=i+1, column=1).hyperlink.target)

with open('scraped2.csv','w') as fp:
    for fn,href in zip(fns, hrefs):
        fp.write('{},{}\n'.format(fn,href))
hrefs
'''
asfn = []
asstmt = []
cnt = 0
for fn,url in zip(fns,hrefs):
    #fn = 'hold'
    try:
        html = urlopen(url)
    except HTTPError:
        print("couldn't reach {:s}".format(url))
        continue
    soup = BeautifulSoup(html)

    sss = soup.find_all("div", {"class": "syntax_signature"})[0]

    sns = sss.find_all("code", {"class": "synopsis"})

    for sn in sns:
        if any(['{:s}('.format(fn) in cti for cti in sn.contents]):
            asfn.append(fn)
        elif len(sn.contents) == 1:
            assert('(' not in sn.contents[0])
            asstmt.append(sn.contents[0])
        else:
            sn
    cnt +=1 
    if cnt == 100:
        break

with open('MATLABfns.txt','w') as fp:
    for asfni in asfn: fp.write('{:s}\n'.format(asfni))

with open('MATLABstmts.txt','w') as fp:
    for asstmti in asstmt: fp.write('{:s}\n'.format(asstmti))

    
