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
        '''Adds a Node with NAME and VALUE to the network.
        '''
        #Create an empty node object, assign its attributes (name and value)
        node = Node()
        node.name = name
        node.value = value
       
        #Append node to the list of nodes
        self.nodes.append(node)
        
    def join_nodes(self, node_from, node_to, weight):
        '''Adds an Arc joining NODE_FROM to NODE_TO with WEIGHT.
        '''
        # **to do: create an empty arc object, assign its attributes**
        arc = Arc()
        arc.weight = weight
        arc.from_node = node_from
        arc.to_node = node_to
        node_from.arcs_out.append(arc)
        node_to.arcs_in.append(arc)
        
        # append node to the list of nodes
        self.arcs.append(arc)
      
    def read_network(self, filename):
        '''Read data from FILENAME and construct the network.
        
            Each line of FILENAME contains
             - the name of an origin node (first entry)
                - and destination;weight pairs (each pair separated by a comma)
                
        '''
        # **to do**
        # **hint: inspect 'network.txt' so that you understand the file structure**
        # **hint: each source-destination pair needs to be joined
                
        # open the file
        fp = open(filename, 'r')
        
        # get first line
        ln = fp.readline().strip()
        
        # keep looping to the end of the file
        while ln is not '':        
            # split string into source node name and other arcs using split() method for strings
            separate = ln.split(',')
            
            #name of source node found in separate[0]
            from_node_name = separate[0]
            
            #create empty arcs object
            arcs = []
            
            #append the destination nodes and weights to arcs object
            i = len(separate)   #length of separate, to find no. of destination nodes and weights
            #if length of list is greater than 2, i.e. more than one destination node, then append these destination nodes to arcs.
            if i >2:
                for l in range(1,i):
                    arcs.append(separate[l])
                    i=i-1
            #if length of list is 2, i.e. one destination node, then append this destination node and weight to arcs.      
            elif i==2:
                arcs.append(separate[1])
          
            # if node doesn't exist, add to network
            try:
                self.get_node(from_node_name)
            except NetworkError:
                self.add_node(from_node_name)
                
            # get the source node object 
            node = self.get_node(from_node_name)

            # read the arc information and add to network
            for arc in arcs:
                [destination, weight] = arc.split(";")

                # get destination node object and link it to source node
                try:
                    self.get_node(destination) 
                except NetworkError:
                    self.add_node(destination)
                    
                destination = self.get_node(destination)
                
                #join nodes
                self.join_nodes(node, destination, weight)
             
            # get next line
            ln = fp.readline().strip()

# **this class is incomplete, you must complete it as part of the lab task**
#                 ----------
class NetworkNZ(Network):
    ''' Derived Network class, for NZ networks.
    '''	
    
	# **this method is incomplete, you must complete it as part of the lab task**
    def read_network(self, directory):

       
        #find nz_network
        folders = glob(directory)
        
        #find station_data.txt files in directory
        filenames = glob("./*/*/**station*") 
        
        #for each of the station files
        for filename in filenames:  
        #open node text file
            fp = open(filename, 'r')

            #read first line
            ln = fp.readline().strip()
                
            #split first line
            (code, name) = ln.split(':')
            name = name.strip()  #remove blank spaces from name   
            
            #get next line
            ln = fp.readline().strip()
                
            #split next line to get x value
            (xname, xvalue) = ln.split(':') 
            x = int(xvalue)
                
            #read next line
            ln = fp.readline().strip()
            
            #split next line to get y value
            (yname, yvalue) = ln.split(':') 
            y = int(yvalue)
            value = [x, y]
            
            #if node doesn't exist add to network
            try:
                self.get_node(name)
            except NetworkError:
                self.add_node(name, value)
                
        #find nz_network
        folders = glob(directory)
        
        #find connections folder
        connectionfiles = glob("./*/**connections*/*")

        #for each connection
        for connection in connectionfiles:
            capacity = 0

            #find name of source and destination nodes
            delete = connection.split('\\')
            nametxt = delete[3]
            nameoftofromtxt = nametxt.split('.')
            nameoftofrom = nameoftofromtxt[0]
            from_node, to_node = nameoftofrom.split('-')
            
            #find capacity column of data, within connection
            data = np.genfromtxt(connection, dtype = None, skip_header = 1, delimiter = ',', usecols = 1)
            
            #number of capacity readings in file
            length = len(data)
            i=[]
            a=0
            
            #Turn data into an array
            while a is not len(data): 
                b = data[a]
                capacity = b+capacity
                i.append(b)
                a = a+1
            capacity = i
               
            #Find some of all capacity readings, divide by length. This will give the average capacity i.e. arc.weight    
            capacitysum = int((np.sum(capacity)))
            length = int(length)
            weight= capacitysum/length

            #get source and destination nodes
            sourcenode = self.get_node(from_node.strip())
            destination = self.get_node(to_node.strip())

            #Join nodes with arc   
            self.join_nodes(sourcenode, destination, weight)
        
	
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
	
	
		
		
		