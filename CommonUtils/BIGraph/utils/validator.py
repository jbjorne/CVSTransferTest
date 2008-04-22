import os
import re
import inspect
import cElementTree as ET
from BIGraph import *
from BIGraph.core.corpus import Corpus
import libxml2 as L
import networkx as NX

class Validator:
    """
    The data is validated in two parts: XML Schemas in bioinfer.xsd,
    bioinfer.relaxed.xsd, and bioinfer.compatible.xsd specify the
    structure of the xml while 'isValid*'-functions ensure that the
    semantics is valid.
    """
    @classmethod
    def validateFromET(cls,root,target):
        """
        Fully validates the corpus against a specific format.

        @param root: the root node of the corpus
        @type root: cElementTree.Element
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        corpus = Corpus()
        if corpus.readFromET(root):
            return( Validator.validate(corpus,target) )
        else:
            return(False)

    @classmethod
    def validateFromString(cls,xmlstring,target):
        """
        Fully validates the corpus against a specific format.

        @param xmlstring: XML containing the corpus
        @type xmlstring: string 
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        corpus = Corpus()
        if corpus.readFromString(xmlstring):
            return( Validator.validate(corpus,target) )        
        else:
            return(False)

    @classmethod
    def validateFromFile(cls,infile,target):
        """
        Fully validates the corpus against a specific format.

        @param infile: file containing the corpus
        @type infile: file name or open file
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        corpus = Corpus()
        if corpus.readFromFile(infile):
            return( Validator.validate(corpus,target) )
        else:
            return(False)
        
    @classmethod
    def validate(cls,corpus,target):
        """
        Fully validates the corpus against a specific format.

        @param corpus: the data
        @type corpus: Corpus instance
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        printWarning(cls,inspect.stack()[0][3],
                     "Preparing data for xsd validation..")
        xmlstring = corpus.writeToString()
        printWarning(cls,inspect.stack()[0][3],
                     "Prepared")
        xsd = Validator.validateXSD(xmlstring,target)
        semantic = Validator.validateSemantic(corpus,target)
        valid = (xsd and semantic)
        if not valid:
            printError(cls,inspect.stack()[0][3],
                       "Data not valid")
        return(valid)

    @classmethod
    def validateXSD(cls,xmlstring,target):
        """
        Performs XSD validation on the data.

        @param xmlstring: XML containing the corpus
        @type xmlstring: string 
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Validating against '%s' XSD.."%(target))

        curdir = os.path.dirname(globals()['__file__'])
        if target=="new":
            xsd="%s/../bioinfer.xsd"%curdir
        elif target=="relaxed":
            xsd="%s/../bioinfer.relaxed.xsd"%curdir
        elif target=="compatible":
            xsd="%s/../bioinfer.relaxed.xsd"%curdir
        else:
            printError(cls,inspect.stack()[0][3],"Cannot validate '%s' format"%target)
            return(False)
        
        doc = L.parseDoc(xmlstring)
        schemaCtxt = L.schemaNewParserCtxt(xsd)
        schema = schemaCtxt.schemaParse()
        validatorCtxt = schema.schemaNewValidCtxt()

        exitstatus = validatorCtxt.schemaValidateDoc(doc)
        valid = (exitstatus==0)
        if valid:
            printMessage(cls,inspect.stack()[0][3],"Valid XML")
        else:
            printError(cls,inspect.stack()[0][3],"Invalid XML")
        return(valid)

    @classmethod
    def validateSemantic(cls,corpus,target):
        """
        Performs semantic validation on the data.

        @param corpus: the corpus
        @type corpus: Corpus instance
        @param target: target format
        @type target: string

        @return: validity of the corpus
        @rtype: boolean
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Validating against '%s' semantics.."%(target))

        if target=="new":
            testfunction = Validator.isValidNew
        elif target=="relaxed":
            testfunction = Validator.isValidRelaxed
        elif target=="compatible":
            testfunction = Validator.isValidCompatible
        else:
            printError(cls,inspect.stack()[0][3],"Cannot validate '%s' format"%target)
            return(False)
        
        valid = testfunction(corpus)
        if valid:
            printMessage(cls,inspect.stack()[0][3],"Valid semantics")
        else:
            printError(cls,inspect.stack()[0][3],"Invalid semantics")
        return(valid)

    @classmethod
    def checkSubtokens(cls,corpus):
        valid = True
        # each offset must be assigned to exactly one subtoken 
        for sentence in corpus.sentences:
            maxOffset = len(sentence.text)-1
            offsets_all = range(maxOffset)
            offsets_used = []
            for subtoken in sentence.subtokens.values():
                offsets_used.extend(range(subtoken.offset_bgn,
                                          subtoken.offset_end+1))
            for x in offsets_used:
                try:
                    offsets_all.remove(x)
                except ValueError, e:
                    printError(cls,inspect.stack()[0][3],
                               "Double-assigned offset %s"%x)
                    valid = False
            for x in offsets_all:
                    printError(cls,inspect.stack()[0][3],
                               "Non-assigned offset %s"%x)
                    valid = False
        return(valid)

    @classmethod
    def checkDeptokens(cls,corpus):
        reWs = re.compile(r'^\s*$')
        valid = True
        # each non-whitespace subtoken must be assigned
        # exactly one reltoken
        for sentence in corpus.sentences:
            seen = {}
            for deptoken in sentence.deptokens.values():
                for x in deptoken.getNested():
                    if reWs.search(x.text):
                        printWarning(cls,inspect.stack()[0][3],
                                     "Whitespace subtoken %s in token %s"%
                                     (x.id,deptoken.id))
                    if x.id in seen.keys():
                        printError(cls,inspect.stack()[0][3],
                                   "Double-assigned subtoken %s (tokens %s and %s)"%
                                   (x.id,seen[x],deptoken.id))
                        valid = False
                    else:
                        seen[x.id] = deptoken.id
            for subtoken in sentence.subtokens.values():
                if not subtoken.id in seen and not reWs.search(subtoken.text):
                    printError(cls,inspect.stack()[0][3],
                               "Non-assigned subtoken %s"%(subtoken.id))
                    valid = False
        return(valid)

    @classmethod
    def checkReltokens(cls,corpus):
        valid = True
        # each reltoken must contain a unique combination of subtokens
        for sentence in corpus.sentences:
            seen = {}
            for reltoken in sentence.reltokens.values():
                uniStr = reltoken.getUniStr()
                if seen.has_key(uniStr):
                    printError(cls,inspect.stack()[0][3],
                               "Double-assigned combination of nested subtokens %s (%s and %s)"%
                               (uniStr,seen[uniStr],reltoken.id))
                    valid = False
                else:
                    seen[uniStr] = reltoken.id
        return(valid)

    @classmethod
    def checkRelentitytypes(cls,corpus):
        valid = True
        # if group=='Process', effect & symmetric must be defined
        for node in corpus.vocabularies['relentityvocabulary'].getNodes():
            if node.group=='Process':
                if node.effect==None:
                    printError(cls,inspect.stack()[0][3],
                               "Non-assigned 'effect' in type %s"%(node.type))
                    valid = False
                if node.symmetric==None:
                    printError(cls,inspect.stack()[0][3],
                               "Non-assigned 'symmetric' in type %s"%(node.type))
                    valid = False
        return(valid)
        

    @classmethod
    def isValidNew(cls,corpus):
        """
        Performs semantic validation against 'new' format.

        @param corpus: the corpus
        @type corpus: Corpus instance

        @return: validity of the corpus
        @rtype: boolean
        """
        valid = True
        valid = valid and Validator.checkRelentitytypes(corpus)
        # Subtokens do not yet fulfill the requirements
        # valid = valid and Validator.checkSubtokens(corpus)
        valid = valid and Validator.checkDeptokens(corpus)
        valid = valid and Validator.checkReltokens(corpus)
        # 
        return(valid)
        
    @classmethod
    def isValidRelaxed(cls,root):
        """
        Performs semantic validation against 'relaxed' format.

        @param root: the root node of the corpus
        @type root: cElementTree.Element

        @return: validity of the corpus
        @rtype: boolean
        """
        valid = True
        # no anonymous entities allowed
        for a in root.getiterator("reltoken"):
            if len(a)==0 and a.attrib['relaxed_tag']=="entity":
                printError(cls,inspect.stack()[1][3],"Reltoken of physical type with no nested subtokens")
                valid = False
        return(valid)
        
    @classmethod
    def isValidCompatible(cls,root):
        """
        Performs semantic validation against 'compatible' format.

        @param root: the root node of the corpus
        @type root: cElementTree.Element

        @return: validity of the corpus
        @rtype: boolean
        """
        valid = True
        # the order of node types in chains is restricted
        # (this would be easier if the data was in a Corpus-instance)
        allowed = NX.XDiGraph(selfloops=True)

        # continue from here!
        allowed.add_edge('Physical','Physical')
        allowed.add_edge('Property','Physical')
        allowed.add_edge('Process','Physical')
        allowed.add_edge('Regulation','Physical')

        allowed.add_edge('Property','Property')
        allowed.add_edge('Process','Property')
        allowed.add_edge('Regulation','Property')

        allowed.add_edge('Property','Process')
#         allowed.add_edge('Process','Process')
        allowed.add_edge('Regulation','Process')

        allowed.add_edge('Property','Regulation')
#         allowed.add_edge('Process','Regulation')
        allowed.add_edge('Regulation','Regulation')

        mapping = {}
        for a in root.find("ontologies").findall("ontology"):
            if a.attrib['id']=='interaction':
                for x in a.getiterator("ontnode"):
                    if x.attrib.has_key('effect') and x.attrib['effect'].endswith('regulation'):
                        t = 'Regulation'
                    else:
                        t = x.attrib['onttype']
                    mapping[x.attrib['id']] = t
        
        for a in root.getiterator("relannotation"):
            t2type = dict( [(x.attrib['id'],x.attrib['type'])
                            for x in a.findall("reltoken")] )
            n2t = dict( [(x.attrib['id'],x.attrib['token'])
                         for x in a.findall("relnode")] )
            for x in a.findall("reledge"):
                bt = t2type[n2t[x.attrib['bgn']]]
                et = t2type[n2t[x.attrib['end']]]
                bgn = mapping[bt]
                end = mapping[et]
                if not allowed.has_edge(bgn,end):
                    printError(cls,inspect.stack()[1][3],
                               "%s -- %s (%s) -> %s (%s) is not a valid edge"%
                               (x.attrib['id'].split('.')[1],bgn,bt,end,et))
                    valid = False
            
        return(valid)
