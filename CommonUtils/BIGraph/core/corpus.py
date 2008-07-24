import inspect
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET
from BIGraph import *
from BIGraph.core.ontology import *
from BIGraph.core.sentence import Sentence

class Corpus:
    """
    The Corpus class handles the top-level I/O. The data structure in
    memory is processed from/to the new style XML format. 
    """
    def __init__(self):
        """
        Initialisation produces an empty corpus.
        """
        self.vocabularies = {}
        """the BioInfer vocabularies as a dictionary (by id) of L{vocabulary.Vocabulary} objects"""
        self.sentences = []
        """the corpus sentences as a list of L{sentence.Sentence} objects"""

# ----
# functions for reading and writing corpus
# ----

    def readFromString(self,xmlstring):
        """
        Reads the corpus from a string.

        @param xmlstring: input xml
        @type  xmlstring: string
        """
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Parsing BioInfer from string..")
        try:
            root = ET.fromstring(xmlstring)
        except Exception, e:
            printError(self.__class__,inspect.stack()[0][3],
                       "Failed to parse: %s"%(e))
            return(False)
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Parsed")
        self.analyse(root)
        return(True)
        
    def readFromFile(self,infile):
        """
        Reads the corpus from a XML file.

        @param infile: input file (directly passed to cElementTree.parse)
        @type  infile: file name or open file
        """
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Parsing BioInfer from %s.."%(infile))
        try:
            root = ET.parse(infile).getroot()
        except Exception, e:
            printError(self.__class__,inspect.stack()[0][3],
                       "Failed to parse '%s': %s"%(infile, e))
            return(False)
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Parsed")
        self.analyse(root)
        return(True)

    def readFromET(self,root):
        """
        Reads the corpus from cElementTree.Element (root node obtained
        with getroot() method).

        @param root: the root node
        @type root: cElementTree.Element        
        """
        self.analyse(root)
        return(True)

    def read(self,data):
        """
        Alias for readFromFile
        """
        return( self.readFromFile(data) )
    
    def analyse(self,root):
        """
        Converts cElementTree.Element into class structure
        """
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Analysing the corpus..")
        Corpus.__init__(self)
        # vocabularies
        for a in root.find("vocabularies"):
            uid = a.tag
            if uid=="depentityvocabulary":
                tmp = DepentityVocabulary(**a.attrib)
            elif uid=="depedgevocabulary":
                tmp = DepedgeVocabulary(**a.attrib)
            elif uid=="relentityvocabulary":
                tmp = RelentityVocabulary(**a.attrib)
            elif uid=="reledgevocabulary":
                tmp = ReledgeVocabulary(**a.attrib)
            else:
                tmp = Vocabulary(**a.attrib)
            tmp.setNode(a)
            self.vocabularies[uid] = tmp
        # sentences
        for a in root.find("sentences").findall("sentence"):
            tmp = Sentence()
            tmp.setNode(a)
            self.sentences.append(tmp)
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Analysed")

    def write(self,out):
        """
        Alias for writeToFile
        """
        self.writeToFile(out)

    def writeToFile(self,outfile):
        """
        Writes the corpus to a XML file. Indentation.

        @param outfile: output file
        @type  outfile: file name or open file
        """
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Writing BioInfer to %s..."%(outfile))
        if type(outfile)==type(''):
            try:
                tmp = open(outfile,'w')
            except Exception, e:
                printError(self.__class__,inspect.stack()[0][3],
                           "Failed to open file '%s': %s"%(outfile, e))
                return(False)
        else:
            tmp = outfile
        corpus = self.getNode()
        tmp.write('<?xml version="1.0" encoding="UTF-8"?>'+"\n")
        ET.ElementTree(corpus).write(tmp)
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Written")
        return(True)

    def writeToString(self):
        """
        Writes the corpus to a string. Indentation.

        @return: output xml
        @rtype: string
        """
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Writing BioInfer to string...")
        corpus = self.getNode()
        xmlstring = '<?xml version="1.0" encoding="UTF-8"?>'+"\n"
        xmlstring += ET.tostring(corpus)
        printMessage(self.__class__,inspect.stack()[0][3],
                     "Written")
        return(xmlstring)

    def writeToET(self):
        """
        Writes the corpus to cElementTree.Element. Indentation.

        @return: the root node
        @rtype: cElementTree.Element
        """
        return(self.getNode())
    
    def getNode(self):
        """
        Returns the content of the sentence as cElementTree.Element

        @return: sentence node
        @rtype: cElementTree.Element
        """
        corpus = ET.Element("corpus")
        corpus.attrib['id'] = 'bioinfer'
        ontologies = ET.Element("vocabularies")
        corpus.append(ontologies)
        for a in sorted(self.vocabularies.keys()):
            tmp = self.vocabularies[a].getNode()
            ontologies.append(tmp)
        sentences = ET.Element("sentences")
        corpus.append(sentences)
        for a in self.sentences:
            sentences.append(a.getNode())
        indent(corpus)
        return(corpus)
