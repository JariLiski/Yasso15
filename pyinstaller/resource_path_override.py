import sys
import os


"""This class will extend the original resource_path function so that it
will always point to the archive_path instead of whatever was frozen into it.
WARNING: Do not create an instance of this class before the archives have been extracted!
"""
class ResourcePathOverride(object):    
    resource_path_orig = None
    archive_path = None
    
    def __init__(self, archive_path):
        import enthought.resource.resource_path #here, so that you can import the module freely (at least in theory)
        self.resource_path_orig = enthought.resource.resource_path.resource_path
        self.archive_path = archive_path
        enthought.resource.resource_path.resource_path = self.resource_path
        #print "Replaced", self.resource_path_orig, "with", self.resource_path, #DEBUG
        #print "as proven by", enthought.resource.resource_path.resource_path #DEBUG
         
    def resource_path(self, level = 2):
        path = self.resource_path_orig(level+1)
        #print "KEY INTEL, PATH INFO:", path #DEBUG
        path = path.rsplit(''.join((os.path.sep, 'enthought', os.path.sep)), 1)
        #print "path", path #DEBUG
        root = path[0].rsplit(os.path.sep, 1)
        #print "root", root #DEBUG
        path = os.path.join(self.archive_path, self.get_pkg_name(root[1]), 'enthought', path[1])
        #print "final", path #DEBUG
        return path        
        
    def get_pkg_name(self, path):
        """This function must mirror the list in yasso.spec
        """
        if path.startswith('Traits-'): 
            return 'traits'
        if path.startswith('TraitsGUI'): 
            return 'traitsgui'
        if path.startswith('TraitsBackendWX'): 
            return 'traitswx'
        if path.startswith('Enable'): 
            return 'enable'
        if path.startswith('Enthought'): 
            return 'enthought'
        if path.startswith('Chaco'): 
            return 'chaco'