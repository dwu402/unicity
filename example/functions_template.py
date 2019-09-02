import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from glob import glob
class Station(object):
    def __init__(self):
        self.id = None
        self.val = None
        self.cons_in = []
        self.cons_out = []
class Connection(object):
    def __init__(self):
        self.wgt=None
        self.to_stat = None
        self.from_stat = None
class GridError(Exception):
    pass
class Grid(object):
    def __init__(self):
        self.stations = []
        self.connections = []
    def query_station(self, name):
        for stat in self.stations:
            if stat.id == name:
                return stat
        raise GridError
    def add_station(self, name, value=None):
        stat = None     
    def add_connection(self, stat_from, stat_to, weight):
        pass
    def read(self, filename):
        fp = open(filename, 'r')
        ln = fp.readline().strip()
        while ln is not '':        
            try:
                self.query_station(stat_name)           
            except GridError:
                self.add_station(stat_name)
            for conn in conns:
                pass
class Roads(Grid):
    def read(self, directory):
        pass
    