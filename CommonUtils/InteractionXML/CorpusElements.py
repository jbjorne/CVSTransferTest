from SentenceElements import *
import types
import cElementTreeUtils as ETUtils

def loadCorpus(filename, parse=None, tokenization=None, removeIntersentenceInteractions=True, removeNameInfo=False):
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import cElementTree as ET
    import sys, gzip
    
    if type(filename) == types.StringType:
        print >> sys.stderr, "Loading corpus file", filename
    corpusTree = ETUtils.ETFromObj(filename)
    corpusRoot = corpusTree.getroot()
    return CorpusElements(corpusRoot, parse, tokenization, removeIntersentenceInteractions, corpusTree, removeNameInfo)

class CorpusElements:
    def __init__(self, rootElement, parse, tokenization=None, removeIntersentenceInteractions=True, tree=None, removeNameInfo=False):
        self.tree = tree
        self.rootElement = rootElement
        self.documents = rootElement.findall("document")
        self.documentsById = {}
        self.sentencesById = {}
        self.sentencesByOrigId = {}
        self.sentences = []
        self.documentSentences = []
        for documentElement in self.documents:
            self.documentsById[documentElement.attrib["id"]] = documentElement
            sentenceElements = documentElement.findall("sentence")
            self.documentSentences.append([])
            for sentenceElement in sentenceElements:
                sentenceObj = SentenceElements(sentenceElement, parse, tokenization, removeIntersentenceInteractions)
                self.sentencesById[sentenceElement.attrib["id"]] = sentenceObj
                if sentenceElement.attrib.has_key("origId"):
                    self.sentencesByOrigId[sentenceElement.attrib["origId"]] = sentenceObj
                self.sentences.append(sentenceObj)
                self.documentSentences[-1].append(sentenceObj)
