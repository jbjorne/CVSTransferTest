try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET
import inspect
from BIGraph import *

class Node(SimpleElement):
    """
    Generic vocabulary node. Provides methods to describe the vocabulary structure.
    """
    def __init__(self,**kwargs):
        SimpleElement.__init__(self,**kwargs)
        self.setVars(['type'],**kwargs)
        self.children = []
        
    def addChild(self,child):
        """
        Adds a child node.

        @param child: child node
        @type child: Node object
        """
        self.children.append(child)

    def getNode(self):
        """
        Returns cElementTree.Element of the node.

        @return: the node
        @rtype: cElementTree.Element
        """
        node = SimpleElement.getNode(self)
        node.tag = 'vocabularynode'
        del node.attrib['children']
        for a in self.children:
            node.append(a.getNode())
        return(node)

class DepentityNode(Node):
    """
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns cElementTree.Element of the node.

        @return: the node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'depentitytype'
        return(node)

class DepedgeNode(Node):
    """
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns cElementTree.Element of the node.

        @return: the node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'depedgetype'
        return(node)

class RelentityNode(Node):
    """
    RelentityNode extends Node with attributes
    'symmetric','effect','group'.
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)
        self.setVars(['symmetric','effect','group'],**kwargs)

    def getNode(self):
        """
        Returns cElementTree.Element of the node.

        @return: the node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'relentitytype'
        return(node)

class ReledgeNode(Node):
    """
    """
    def __init__(self,**kwargs):
        Node.__init__(self,**kwargs)

    def getNode(self):
        """
        Returns cElementTree.Element of the node.

        @return: the node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'reledgetype'
        return(node)

class Vocabulary(Node):
    """
    Data structure for ontologies. This class provides methods to get
    properties and hierarchical relationships of nodes. The vocabulary
    itself is the root node.
    """
    def __init__(self,**kwargs):
        """
        Initialisation of an empty vocabulary.
        """
        Node.__init__(self,**kwargs)
        self.id2node = {}
        """Mapping of each type into its node"""
        self.id2nested = {}
        """Mapping of each type into its nested types"""

    def _newNode(self,node):
        """
        Helper function for creating nodes of correct type.
        """
        return( Node(**node.attrib) )
    
    def setNode(self,root):
        """
        Sets a new content for the vocabulary.

        @param root: root node of the vocabulary
        @type root: cElementTree.Element
        """
        Vocabulary.__init__(self)
        if self.isValid(root):
            nodes = [n for n in root.getiterator() if n!=root]
            for a in nodes:
                uid = a.attrib['type']
                self.id2node[uid] = self._newNode(a)
                # - keys are the names of the nodes under the node 'r'
                # - values are lists of the names of the recursive children
                self.id2nested[uid] = [x.attrib["type"]
                                       for x in a.getiterator()]
            for a in nodes:
                uid1 = a.attrib['type']
                for x in a[:]:
                    uid2 = x.attrib['type']
                    self.id2node[uid1].addChild(self.id2node[uid2])
            for x in root[:]:
                uid2 = x.attrib['type']
                self.addChild(self.id2node[uid2])
        else:
            printError(self.__class__,inspect.stack()[0][3],
                       "Invalid vocabulary (%s)"%(root.attrib['type']))

    def getNode(self):
        """
        Returns the root node of the vocabulary
        
        @return: root node
        @rtype: cElementTree.Element
        """
        node = Node.getNode(self)
        node.tag = 'vocabulary'
        del node.attrib['id2node']
        del node.attrib['id2nested']
        return(node)

    def isNested(self,parent,child):
        """
        True if and only if 'child' is below 'parent' in the hierarchy
        or 'child'=='parent'

        @param parent: parent node type
        @type parent: string
        @param child: child node type
        @type child: string
        
        @return: child =< parent
        @rtype: boolean
        """
        return( child in self.id2nested[parent] )

    def isValid(self,root):
        """
        Provided that XML passes XSD validation, the vocabulary is valid

        @param root: root node the vocabulary
        @type root: cElementTree.Element
        @return: validity of the vocabulary
        @rtype: boolean
        """
        return(True)

class DepentityVocabulary(Vocabulary):
    """
    Identical to Vocabulary.
    """
    def __init__(self):
        Vocabulary.__init__(self)

    def _newNode(self,node):
        """
        (Use RelentityNodes as inner nodes.)
        """
        return( DepentityNode(**node.attrib) )

    def getNode(self):
        """
        Returns the root node of the vocabulary
        
        @return: root node
        @rtype: cElementTree.Element
        """
        node = Vocabulary.getNode(self)
        node.tag = 'depentityvocabulary'
        return(node)

class DepedgeVocabulary(Vocabulary):
    """
    Identical to Vocabulary.
    """
    def __init__(self):
        Vocabulary.__init__(self)

    def _newNode(self,node):
        """
        (Use RelentityNodes as inner nodes.)
        """
        return( DepedgeNode(**node.attrib) )

    def getNode(self):
        """
        Returns the root node of the vocabulary
        
        @return: root node
        @rtype: cElementTree.Element
        """
        node = Vocabulary.getNode(self)
        node.tag = 'depedgevocabulary'
        return(node)

class RelentityVocabulary(Vocabulary):
    """
    RelentityVocabulary extends the generic vocabulary by using
    RelentityNodes.
    """
    def __init__(self):
        Vocabulary.__init__(self)

    def _newNode(self,node):
        """
        (Use RelentityNodes as inner nodes.)
        """
        return( RelentityNode(**node.attrib) )

    def getNode(self):
        """
        Returns the root node of the vocabulary
        
        @return: root node
        @rtype: cElementTree.Element
        """
        node = Vocabulary.getNode(self)
        node.tag = 'relentityvocabulary'
        return(node)

    def isValid(self,root):
        """
        Validity checks. Each node (except the root) must have
        'group' attribute. In addition, each node of type 'Process'
        must have 'effect' and 'symmetric' attributes.

        @param root: root node the vocabulary
        @type root: cElementTree.Element
        @return: validity of the vocabulary
        @rtype: boolean
        """
        if not Vocabulary.isValid(self,root):
            return(False)
        for a in root.getiterator():
            if a==root:
                continue
            uid = a.attrib['type']
            if not a.attrib.has_key('group'):
                printError(self.__class__,inspect.stack()[0][3],
                           "group attribute missing (%s)"%(uid))
                return(False)
            if a.attrib['group']=="Process":
                if not a.attrib.has_key('effect'):
                    printError(self.__class__,inspect.stack()[0][3],
                               "effect attribute missing (%s)"%(uid))
                    return(False)
                if not a.attrib.has_key('symmetric'):
                    printError(self.__class__,inspect.stack()[0][3],
                               "symmetric attribute missing (%s)"%(uid))
                    return(False)
        return(True)
    
    def isSymmetric(self,uid):
        """
        True if and only if the 'symmetric' attribute is True

        @param uid: node id (i.e. type)
        @type uid: string
        @return: symmetric==True
        @rtype: boolean
        """
        return( self.id2node[uid].symmetric )
    
    def isPhysical(self,uid):
        """
        True if and only if the 'group' attribute is 'Physical'
        
        @param uid: node id (i.e. type)
        @type uid: string
        @return: group=='Physical'
        @rtype: boolean
        """
        return( self.id2node[uid].group=="Physical" )

    def isProperty(self,uid):
        """
        True if and only if the 'group' attribute is 'Property'
        
        @param uid: node id (i.e. type)
        @type uid: string
        @return: group=='Property'
        @rtype: boolean
        """
        return( self.id2node[uid].group=="Property" )

    def isProcess(self,uid):
        """
        True if and only if the 'group' attribute is 'Process'
        
        @param uid: node id (i.e. type)
        @type uid: string
        @return: group=='Process'
        @rtype: boolean
        """
        return( self.id2node[uid].group=="Process" )

    def getPhysicalType(self,uid):
        """
        Returns the physical type (Protein/DNA/RNA) of the node (or
        empty string for non-physical nodes).
        
        @param uid: node id (i.e. type)
        @type uid: string
        @return: physical type
        @rtype: Protein|DNA|RNA|<empty string>
        """
        if self.isNested('Protein',uid):
            return('Protein')
        elif self.isNested('Peptide',uid):
            return('Protein')
        elif self.isNested('DNA',uid):
            return('DNA')
        elif self.isNested('RNA',uid):
            return('RNA')
        else:
            return('')

class ReledgeVocabulary(Vocabulary):
    """
    Identical to Vocabulary.
    """
    def __init__(self):
        Vocabulary.__init__(self)

    def _newNode(self,node):
        """
        (Use RelentityNodes as inner nodes.)
        """
        return( ReledgeNode(**node.attrib) )

    def getNode(self):
        """
        Returns the root node of the vocabulary
        
        @return: root node
        @rtype: cElementTree.Element
        """
        node = Vocabulary.getNode(self)
        node.tag = 'reledgevocabulary'
        return(node)
