"""
BIGraph package allows for representing BioInfer annotation as a set of graphs.
It includes methods for transforming the graph representation to and from
various XML formats. Addionally, it includes modules for manipulating the graph
representation.

The compatible format is simply a refactoring of the old format. It
can be read into Corpus instance but no methods are available. The
relaxed format is obtained by manipulating the comptaible format in
such a way that the data is fully valid with the methods. This
conversion causes minor losses in the data. These two formats can be
converted back to the old format. The new format is obtained from the
relaxed format by deleting all information that is needed in the
conversion back to the old format but that is not required anymore in
the graph representation.

The validity of the data is checked in two parts. The structure of the
XML is validated against XSD and the semantics of the data is checked
with isValid*-functions.

The graph representation is based on the following concepts:
  - The original text is split into subtokens which fully cover the text.
  - The syntactic annotation consists of deptokens (dep for dependency) and
  their dependencies (depnodes and depedges) represented as a directed graph.
  - The interaction annotation consists of reltokens (rel for relationship)
  and their dependencies (relnodes and reledges) represented as a directed graph.

The module core includes the classes for I/O. The module refiners contains
classes for transforming the annotation in several ways. The module utils
contains classes and functions that supplement other classes. The module apps
contains classes that can be used to create user-interfaces. The module
binariser consists of classes involved in the binarisation of the corpus.
"""

import sys
import string
import cElementTree as ET

class SimpleElement:
    """
    SimpleElement is the very basic class for all elements. It
    provides functions to initialise the element and to get the
    content of the element as cElementTree.Element object.

    Each SimpleElement (or subclass) object has 'id' instance
    variable.
    """
    def __init__(self,**kwargs):
        self.setVars(['id'],**kwargs)
        self.setRelaxedVars(**kwargs)

    def _setVar(self,k,v):
        if v=="True":
            v=True
        elif v=="False":
            v=False
# This messes 'text' attributes!
#         elif not v==None:
#             try:
#                 v=int(v)
#             except ValueError, e:
#                 pass
        self.__dict__[k] = v
        
    def setVars(self,inlist,**kwargs):
        """
        Sets the instance variables.

        @param inlist: allowed attributes
        @type inlist: list
        @param kwargs: attribute values
        @type kwargs: keyword arguments
        """
        for k in inlist:
            if kwargs.has_key(k):
                self._setVar(k,kwargs[k])
            else:
                self._setVar(k,None)

    def setRelaxedVars(self,**kwargs):
        """
        Sets any instance variable that begins with 'relaxed_'.

        @param kwargs: attribute values
        @type kwargs: keyword arguments
        """
        for k in kwargs.keys():
            if k.startswith('relaxed_'):
                self._setVar(k,kwargs[k])
        
    def getNode(self):
        """
        Returns the content of the element as cElementTree.Element
        object. Instance variables that have value None are not
        included as attributes.
        """
        node = ET.Element('element')
        for a in self.__dict__:
            if self.__dict__[a]==None:
                continue
            node.attrib[a] = str(self.__dict__[a])
        return(node)

class Increment:
    """
    Increment instance gives all non-negative integers starting from
    zero. This is used to assign running ids for elements.
    """
    def __init__(self):
        self.cur = -1

    def get(self):
        """
        Returns the next id.

        @return: id
        @rtype: string representing an integer
        """
        self.cur += 1
        return(str(self.cur))

class FreeIdIter:
    """
    FreeIdIter is similar to Increment but in initialisation it is
    given a list of already used ids.
    """
    def __init__(self,used):
        """
        @param used: the used ids
        @type used: list
        """
        self.used = used
        self.cur = 0

    def get(self):
        """
        Returns the next id.

        @return: id
        @rtype: string representing an integer
        """
        while self.cur in self.used:
            self.cur += 1
        self.used.append(self.cur)
        return(str(self.cur))

def printMessage(process,function,message):
    """
    Prints a message to stderr in a fixed format.
    """
    sys.stderr.write("MESSAGE by %s@%s: %s\n"%
                     (function,
                      str(process).split('.')[-1],
                      message))

def printWarning(process,function,message):
    """
    Prints a warning message to stderr in a fixed format. A warning does not
    imply a failure in the process although it is possible.
    """
    sys.stderr.write("WARNING by %s@%s: %s\n"%
                     (function,
                      str(process).split('.')[-1],
                      message))

def printError(process,function,message):
    """
    Prints an error message to stderr in a fixed format. An error indicates
    that the function failed even if a result was produced.
    """
    sys.stderr.write("ERROR by %s@%s: %s\n"%
                     (function,
                      str(process).split('.')[-1],
                      message))

def indent(elem, level=0):
    """
    In-place indentation of XML (in cElementTree.Element object).
    This function was provided by Filip Salomonsson. See
    http://infix.se/2007/02/06/gentlemen-indent-your-xml.
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "  "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
