# imports
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from glob import glob

	
# these classes are complete, do not modify them
class Node(object):
	def __init__(self):
		self.name = None
		self.value = None
		self.arcs_in = []
		self.arcs_out = []
class Arc(object):
	def __init__(self):
		self.weight=None
		self.to_node = None
		self.from_node = None
class NetworkError(Exception):
	'''An error to raise when violations occur.
	'''
	pass
		
	
# **this class is incomplete, you must complete it as part of the lab task**
#                 ----------
class Network(object):
	''' Basic network class.
	'''
	# these methods are complete, do not modify them
	def __init__(self):
		self.nodes = []
		self.arcs = []
	def get_node(self, name):
		''' Loops through the list of nodes and returns the one with NAME.
		
		    Returns NetworkError if node does not exist.
		'''
		# loop through list of nodes until node found
		for node in self.nodes:
			if node.name == name:
				return node
		
		raise NetworkError
	def display(self):
		''' Print information about the network.
		'''
		# print nodes
		print('network has {:d} nodes: '.format(len(self.nodes))+(len(self.nodes)*'{}, ').format(*(nd.name for nd in self.nodes)))
		# print arcs
		for arc in self.arcs:
			print ('{} --> {} with weight {}'.format(arc.from_node.name, arc.to_node.name, arc.weight))
	
	# **these methods are incomplete, you must complete them as part of the lab task**
	def add_node(self, name, value=None):
		self.add_node('name', value)
		node.name = name
		node.value = value
		#ndname = self.get_node('name')
		#assert(ndname.name == 'name')
		#assert(ndname.value == value)
		# **to do: create an empty node object, assign its attributes**
		# **hint: how are empty network objects created in lab5_task1.py?**
		# **hint: how are names and values assigned in the __init__ method for node?**
		___
		
		# append node to the list of nodes
		self.nodes.append(node)
		
	def join_nodes(self, node_from, node_to, weight):
		arc = Arc()
		arc.weight= weight
		arc.to_node = node_to
		arc.from_node = node_from
		# **to do: create an empty arc object, assign its attributes**
		# **hint: both node objects have arcs_in and arcs_out objects - how should these be modified**
		___
		
	def read_network(self, filename):
		'''Read data from FILENAME and construct the network.
		
			Each line of FILENAME contains
			 - the name of an origin node (first entry)
			 - and destination;weight pairs (each pair separated by a comma)
			 
		'''
		# **to do**
		# **hint: inspect 'network.txt' so that you understand the file structure**
		# **hint: each source-destination pair needs to be joined
		
		# **some useful (incomplete) code snippets**
		# ln.split
		#
		# 
				
		# open the file
		fp = open(filename, 'r')
		
		# get first line
		ln = fp.readline().strip()
		while ln is not '':        # keep looping to the end of the file
			# split string into source node name and other arcs using split() method for strings
			ln.split(",")
			ln.split(";")
			# if node doesn't exist, add to network
			try:
				self.get_node(from_node_name)
			except NetworkError:
				self.add_node(from_node_name)
				
			# get the source node object
			node_source = ln[0]
				
			# read the arc information and add to network
			for arc in arcs:
				# parse arc information
				node_wgt = ln[3]
				node_wgt2 = ln[5]
				
				# get destination node object and link it to source node
				node_dest = ln[2]
				node_dest2 = ln[4]
				
				join_node(self, node_source, node_dest, node_wgt)
				join_node(self, node_source, node_dest2, node_wgt2)
						
			# get next line
			ln = fp.readline().strip()
			
			
# **this class is incomplete, you must complete it as part of the lab task**
#                 ----------
class NetworkNZ(Network):
	''' Derived Network class, for NZ networks.
	'''	
	
	# **this method is incomplete, you must complete it as part of the lab task**
	def read_network(self, directory):
	
		if os.path.isdir(directory) == True
			files = glob('station_data')
			i=0
			for i<= length(files)
				data.filei= np.genfromtxt('files[i]', usecols=(1), dtype = str)
				data.filei.split(" ")
				add_node(NetworkNZ, data[0], None)
				i = i+1
			return
			
			files2 = glob('-')
			j=0
			for j<= length(files2)
				data.filej= np.genfromtxt('files2[j]', dtype = float)
				join_node(NetworkNZ, data[0], None)
				j = j+1
			return 
			
		else print("directory does not exist")
		
		return
		
		''' Read network information from DIRECTORY
		
			Notes:
			------
			Assume that DIRECTORY contains one folder for 
			connections between nodes. All other folders define
			the nodes of the network. 
			
			Each node folder contains a file called station_data.txt that includes a code for the node (this should be used to name the
			node) and x and y values for the node position.
			
			In the connections folder, there is a file for each connection.
			The name of the file indicates which two nodes are connected 
			(from-to) and the contents of the file record the capacity of 
			the connection over the previous 35 years. The connection weight
			is the mean capacity.
		'''
		
		# **some useful functions**
		# glob
		# np.genfromtxt
		# os.path.isdir
		___
	
	# this method is complete, do not modify	
	def show(self, save=None):
		''' Plot the network and optionally save to file SAVE
		'''
		# create figure axes
		fig=plt.figure()
		fig.set_size_inches([10,10])
		ax=plt.axes()
		
		# NZ coastline as background
		img=mpimg.imread('bg.png')
		ax.imshow(img,zorder=1)
	
		# a filthy hack to get coordinates in the right spot...
		for node in self.nodes:
			x,y = node.value
			y = int((y+10)*1.06)
			x -= int(50*y/800.)
			node.value = [x,y]
	
		# draw nodes as text boxes with station names
			# bounding box properties
		props = dict(boxstyle='round', facecolor='white', alpha=1.0)
		for node in self.nodes:
			# extract coordinates
			x,y = node.value
			ax.text(x, y, node.name, ha = 'center', va = 'center', zorder = 2, bbox=props)
			
		# draw connections as lines
		weights = [arc.weight for arc in self.arcs]
			# scale for plotting connections
		wmin = np.min(weights)
		wmax = np.max(weights)
		lmin,lmax = [0.5, 10.0]
		
		# plot connections
		for arc in self.arcs:
			# compute line length, scales with connection size
			lw = (arc.weight-wmin)/(wmax-wmin)*(lmax-lmin)+lmin
			x1,y1 = arc.from_node.value
			x2,y2 = arc.to_node.value
			ax.plot([x1,x2],[y1,y2], '-', lw=lw, color = [0.6,0.6,0.6])
	
		# remove ticks
		ax.set_xticks([])
		ax.set_yticks([])
	
		# display options
		if save:
			# save to file
			plt.savefig(save, dpi=300)
			plt.close()
		else:
			# open figure window in screen
			plt.show()
	
	
		
		
		
		
		
		
		
		
		
			
