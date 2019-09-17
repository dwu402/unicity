# this code modified from https://github.com/agranya99/MOSS-winnowing-seqMatcher
# which in turn implements the winnowing algorithm detailed at
# http://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf
# many of the comments below from the original code

import hashlib
from operator import itemgetter

#sha-1 encoding is used to generate hash values
def hash(text):
    #this function generates hash values
    hashval = hashlib.sha1(text.encode('utf-8'))
    hashval = hashval.hexdigest()[-4 :]
    hashval = int(hashval, 16)  #using last 16 bits of sha-1 digest
    return hashval

#function to form k-grams out of the cleaned up text
def kgrams(text, k = 25):
    tokenList = list(text)
    n = len(tokenList)
    kgs = [None]*(n - k + 1)
    for i in range(n - k + 1):
        kgram = ''.join(tokenList[i : i + k])
        hv = hash(kgram)
        kgs[i] = (kgram, hv, i, i + k)  #k-gram, its hash value, starting and ending positions are stored
    return kgs

#we form windows of hash values and use min-hash to limit the number of fingerprints
def fingerprints(arr, winSize = 4):
    arrLen = len(arr)
    prevMin = 0
    currMin = 0
    n = arrLen - winSize
    windows = [None]*n
    fingerprintList = []
    for i in range(n):
        win = arr[i: i + winSize]  #forming windows
        windows[i] = win
        currMin = i + min(enumerate(win), key=itemgetter(1))[0] 
        if not currMin == prevMin:  #min value of window is stored only if it is not the same as min value of prev window
            fingerprintList.append(arr[currMin])  #reduces the number of fingerprints while maintaining guarantee
            prevMin = currMin  #refer to density of winnowing and guarantee threshold (Stanford paper)

    return fingerprintList

def hashList(arr):
    ''' return hashes from kgram list
    '''
    return [arri[1] for arri in arr]

def toText(arr):
    ''' concatenate text string from token list
    '''
    cleanText = ''.join(str(x[0]) for x in arr)
    return cleanText

def winnow_distance(token1, token2):
    # cat to string
    str1 = toText(token1)       
    str2 = toText(token2)
    #stores k-grams, their hash values and positions
    kGrams1 = kgrams(str1)  
    kGrams2 = kgrams(str2)
    HL1 = hashList(kGrams1)  #hash list derived from k-grams list
    HL2 = hashList(kGrams2)
    fpList1 = fingerprints(HL1)
    fpList2 = fingerprints(HL2)
    points = []
    for i in fpList1:
        for j in fpList2:
            if i == j:   #fingerprints match
                flag = 0
                match = HL1.index(i)   #index of matching fingerprints in hash list, k-grams list
                newStart = kGrams1[match][2]   #start position of matched k-gram
                newEnd = kGrams1[match][3]   #end position
                points.append([newStart, newEnd])
    
    if len(points) == 0:
        return 0.
    points.sort(key = lambda x: x[0])
    
    # calculate length of non-overlapping fingerprint matches
    plagCount = points[0][1] - points[0][0]
    for i,point in enumerate(points[1:]):
        if point[0] < points[i][1]:
            plagCount += point[1] - points[i][1]
        else:
            plagCount += point[1] - point[0]
    
    # scale by length of longest code
    lt1, lt2 = len(str1), len(str2)
    lt = lt1 if lt1>lt2 else lt2

    return plagCount/lt

