import numpy as np
from copy import copy
from warnings import warn

def lu_read(filename):	
	''' 
	Load cofficients of a linear system from a file.
	
	Parameters
	----------
	filename : str
		Name of file containing A and b.
		
	Returns
	-------
	A : np.array
		Matrix for factorisation.
	b : np.array
		RHS vector.
	    
	Notes
    -----
	filename should be point to a textfile 
	
    Examples
    --------
	The syntax for a determined linear system with four unknowns in the text file. 
	1x1 scalar for unknowns (row 0)
	4x4 matrix for coefficients (rows 1 to 4)
	1x4 matrix for RHS vector (row 5)

	4 
	 2.0  3.0 -4.0  2.0
	-4.0 -5.0  6.0 -3.0
	 2.0  2.0  1.0  0.0
	-6.0 -7.0 14.0 -4.0
	 4.0 -8.0  9.0  6.0
	'''
	
	with open(filename, 'r') as fp:
		# Row dimension
		nums = fp.readline().strip()
		row = int(nums)
		
		A = []
		for i in range(row):
			nums = fp.readline().rstrip().split()
			A.append([float(num) for num in nums])
		A = np.array(A)
		
		b = []
		nums = fp.readline().rstrip().split()
		b.append([float(num) for num in nums])
		b = np.array(b)
		
	return A, b.T

def lu_factor(A, pivot=False, display=False):
	"""
	Return LU factors and row swap vector p of matrix A.
	
    Parameters
    ----------
	A : np.array
		Matrix for factorisation. Must be square.
	pivot : Boolean
		Use partial pivoting.
	display : Boolean
		Display matrix factorisation steps.
			
    Returns
    -------
	A : np.array
		Condensed LU factors
	p : np.array
		Row swap vector

    Notes
    -----
	Factorisation occurs in place, i.e., input matrix A is permanently 
	modified by the function. L and U factors are stored in lower and upper 
	triangular parts of the output.
	
    Examples
    --------
	>>>A = np.array([
	[ 2, 3,-4, 2],
	[-4,-5, 6,-3],
	[ 2, 2, 1, 0],
	[-6,-7,14,-4]])
	>>>lu_factor(A, pivot=False, display=False)
	np.array([
	[ 2, 3,-4, 2],
	[-2, 1,-2, 1],
	[ 1,-1, 3,-1],
	[-3, 2, 2, 2]])
	"""
	
	# **this needs to be completed***
	# Precondition (check if a matrix is square)
	# hint: you can use isSquare() function
	#if 
	#	raise 'Matrix L is not square'
	
	# get dimensions of square matrix 
	n = np.shape(A)[0] 	
	
	# create initial row swap vector: p = [0, 1, 2, ... n]
	p = np.arange(n) 		

	# display matrix DO NOT MODIFY
	if display:
		print('')
		print('After {:d} steps'.format(0))
		print('LU=')
		print(A)
		print('p=')
		print(p)

	# loop over each row in the matrix
	for i in range(n-1):		
		
		# Step 2: Row swaps for partial pivoting
		#    DO NOT attempt until Steps 0 and 1 below are confirmed to be working.
		if pivot:
					
			swap = np.argmax(abs(A[i:, i]))								
			p[i] = i+swap												
			
			# Swap rows, if required									
			if i != p[i]:												
				temp = copy(A[i,:])										
				A[i, :] = A[p[i], :]
				A[p[i], :] = temp                                       
				
		# Step 0: Get the pivot value
		pivot_value = A[i,i]											
		
		# Print a warning in case of small pivot value.
		if abs(pivot_value) < zero_tol():
			warn('ENGSCI233:TinyPivot - Pivot value is close to zero')
			
		# Step 1: Perform the row reduction operations 
		for ii in range(i+1, n):										
			multiplier = A[ii, i]/pivot_value							
			for j in range(i, n):	                                    
				A[ii,j] = A[ii,j] - multiplier*A[i,j]                   
			A[ii,i] = multiplier                                        
		 
		# display matrix DO NOT MODIFY
		if display:
			print('')
			print('After {:d} steps'.format(i))
			print('LU=')
			print(A)
			print('p=')
			print(p)
	
	return A, p

def lu_forward_sub(L, b, p=None):
	"""
	**this needs to be completed***	
	
    Parameters
    ----------
			
    Returns
    -------

    Notes
    -----

    Examples
    --------

	"""	
	
	# check shape of L consistent with shape of b (for matrix mult L^T*b)
	assert np.shape(L)[0] == len(b), 'incompatible dimensions of L and b'
	
	# make a copy so RHS vector not destroyed during operations
	y = copy(b)
	
	# Step 0: Get matrix dimension										
	n = np.shape(L)[0] 													
	
	# Step 2: Perform partial pivoting row swaps on RHS
	if p is not None:
		for i in range(n):												
			if i != p[i]:                                               
				y[p[i]],y[i] = copy(y[i]),copy(y[p[i]])                 
				
	# Step 1: Perform forward substitution operations	
	for i in range(n):													
		y[i] = y[i] - np.dot(L[i,:i],y[:i])	                    		
		
	return y

def lu_backward_sub(U, y):
	"""
	**this needs to be completed***	

	"""	
		
	# Preconditions (check consistency of shape)
	assert np.shape(U)[0] == len(y), 'incompatible dimensions of U and y' 	
	
	# Perform backward substitution operations
	n = np.shape(U)[0] 													
	x = 0.*y															
	for i in range(n-1,-1,-1):
		x[i] = 1.*y[i]
		for j in range(i+1,n):
			x[i] = x[i] - U[i,j]*x[j]                  
		x[i] = x[i]/U[i,i]
	
	return x															

def isSquare (A):
	""" Check whether a matrix is square (NxN)
		
    Parameters
    ----------
	A : np.array
		Matrix to be checked
		
    Returns
    -------
	B : Boolean
		True for square matrix, false if not
	
    Notes
    -----
	A should be a numpy array
	
    Examples
    --------
	>>>A = np.array([
	[2, 1],
	[17,4]])
	>>>isSquare (A)
	True
	"""
	# **this needs to be completed***	
	# check if the condition of a square matrix is satisfied
	B = False
	return B

def zero_tol():
	#ZERO_TOL  Tolerance for comparison with zero.
	# See also EPS.
	return 1.e-12
