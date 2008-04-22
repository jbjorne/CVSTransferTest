import sys
import inspect
import copy
import cElementTree as ET
import networkx as NX
from BIGraph import *

class Converter:
    """
    Converter contains methods to convert between different corpus
    formats. The converted corpus is NOT automatically validated.
    """
    @classmethod
    def convertFile(cls,infile,outfile,source,target):
        """
        Converts from 'source' format to 'target' format.

        @param infile: input file
        @type  infile: file name or open file
        @param outfile: output file
        @type  outfile: file name or open file
        @param source: format of source data
        @type source: string
        @param target: format of target data
        @type target: string
        """
        oldRoot = Converter.fileToET(infile)
        newRoot = Converter.convert(oldRoot,source,target)
        ok = Converter.ETToFile(newRoot,outfile)
        return(ok)
    
    @classmethod
    def convertET(cls,root,source,target):
        """
        Converts from 'source' format to 'target' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @param source: format of source data
        @type source: string
        @param target: format of target data
        @type target: string
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        return( Converter.convert(root,source,target) )

    @classmethod
    def convertString(cls,xmlstring,source,target):
        """
        Converts from 'source' format to 'target' format.

        @param xmlstring: input xml document
        @type  xmlstring: string
        @param source: format of source data
        @type source: string
        @param target: format of target data
        @type target: string
        @return: output xml document
        @rtype: string
        """
        oldRoot = ET.fromstring(xmlstring)
        newRoot = Converter.convert(root,source,target)
        return( ET.tostring(newRoot) )

    @classmethod
    def convert(cls,root,source,target):
        """
        Converts from 'source' format to 'target' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @param source: format of source data
        @type source: string
        @param target: format of target data
        @type target: string
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        formats = ['old','compatible','relaxed','new']
        if not source in formats:
            printError(cls,inspect.stack()[0][3],
                       "Unknown format: %s"%source)
            return(root)
        if not target in formats:
            printError(cls,inspect.stack()[0][3],
                       "Unknown format: %s"%target)
            return(root)

        # convert
        if formats.index(source)==formats.index(target):
            printWarning(cls,inspect.stack()[0][3],
                         "Null conversion from %s to %s"%(source,target))
            return(root)
        
        if formats.index(source)<formats.index(target):
            if source=='old' and not source==target:
                root = CorpusConverter.oldToCompatible(root)
                source = 'compatible'
            if source=='compatible' and not source==target:
                root = CorpusConverter.compatibleToRelaxed(root)
                source = 'relaxed'
            if source=='relaxed' and not source==target:
                root = CorpusConverter.relaxedToNew(root)
                source = 'new'
        else:
            if source=='new':
                printError(cls,inspect.stack()[0][3],
                           "Cannot convert from 'new'")
                return(root)
            if source=='relaxed' and not source==target:
                root = CorpusConverter.relaxedToCompatible(root)
                source = 'compatible'
            if source=='compatible' and not source==target:
                root = CorpusConverter.compatibleToOld(root)
                source = 'old'

        for x in root.getiterator():
            x.text=''
            x.tail=''
        indent(root)
        return(root)

    @classmethod
    def fileToET(cls,infile):
        """
        Reads the data from a file into a cElementTree.Element.

        @param infile: input file
        @type  infile: file name or open file
        @return: output object
        @rtype: cElementTree.Element        
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Parsing BioInfer from %s.."%(infile))
        try:
            oldRoot = ET.parse(infile).getroot()
        except Exception, e:
            printError(cls,inspect.stack()[0][3],
                       "Failed to parse '%s': %s"%(infile, e))
            return(False)
        printMessage(cls,inspect.stack()[0][3],
                     "Parsed")
        return(oldRoot)

    @classmethod
    def ETToFile(cls,inobject,outfile):
        """
        Writes the data in a cElementTree.Element into a file.

        @param inobject: input object
        @type  inobject: cElementTree.Element
        @param outfile: output file
        @type  outfile: file name or open file
        @return: boolean for successful run
        @rtype: True or False 
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Writing BioInfer to %s.."%(outfile))
        if type(outfile)==type(''):
            try:
                tmp = open(outfile,'w')
            except Exception, e:
                printError(cls,inspect.stack()[0][3],
                           "Failed to parse '%s': %s"%(infile, e))
                return(False)
        else:
            tmp = outfile
        tmp.write('<?xml version="1.0" encoding="UTF-8"?>'+"\n")
        ET.ElementTree(inobject).write(tmp)
        if type(outfile)==type(''):
            tmp.close()
        printMessage(cls,inspect.stack()[0][3],
                     "Written")
        return(True)

class CorpusConverter:
    """
    Workhorse class. No validation.
    """
    @classmethod
    def oldToCompatible(cls,root):
        """
        Converts 'old' format to 'compatible' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        # major changes
        printMessage(cls,inspect.stack()[0][3],
                     "Converting corpus to compatible format..")

        newRoot = ET.Element("corpus")
        newRoot.attrib['id'] = 'bioinfer'

        ontologies = ET.Element("tmp")
        for a in root.findall("ontology"):
            ontologies.append(a)
        ontologies = OntologyConverter.oldToCompatible(ontologies)
        newRoot.append(ontologies)

        symmetrics = [x.attrib['type']
                      for x in ontologies.getiterator("relentitytype")
                      if x.attrib.has_key("symmetric") and
                      x.attrib['symmetric']=="True"]
        sentences = ET.Element("sentences")
        newRoot.append(sentences)
        for a in root.find("sentences").findall("sentence"):
            sentences.append( SentenceConverter.oldToCompatible(a,symmetrics) )

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)

    @classmethod
    def compatibleToRelaxed(cls,root):
        """
        Converts 'compatible' format to 'relaxed' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting corpus to relaxed format..")

        newRoot = ET.Element("corpus")
        newRoot.attrib['id'] = 'bioinfer'

        ontologies = root.find("vocabularies")
        ontologies = OntologyConverter.compatibleToRelaxed(ontologies)
        newRoot.append(ontologies)

        physicals = [x.attrib['type']
                     for x in ontologies.getiterator("relentitytype")
                     if x.attrib['group']=="Physical"]
        sentences = ET.Element("sentences")
        newRoot.append(sentences)
        for a in root.find("sentences").findall("sentence"):
            sentences.append(SentenceConverter.compatibleToRelaxed(a,
                                                                   physicals))

        # predicatemapping
        tmpMap = dict( [(x.attrib['relaxed_mapsTo'],x.attrib['type'])
                        for x in ontologies.getiterator("relentitytype")
                        if x.attrib.has_key("relaxed_mapsTo")] )
        for x in sentences.getiterator("relentity"):
            if tmpMap.has_key(x.attrib['type']):
                x.attrib['type'] = tmpMap[x.attrib['type']]

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)

    @classmethod
    def relaxedToNew(cls,root):
        """
        Converts 'relaxed' format to 'new' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting corpus to new format..")

        # remove all attributes beginning with 'relaxed_'
        newRoot = copy.deepcopy(root)
        for a in newRoot.getiterator():
            for b in a.attrib.keys():
                if b.startswith("relaxed_"):
                    del a.attrib[b]
        
        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)
    
    @classmethod
    def relaxedToCompatible(cls,root):
        """
        Converts 'relaxed' format to 'compatible' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting corpus to compatible format..")

        newRoot = ET.Element("corpus")
        newRoot.attrib['id'] = 'bioinfer'

        ontologies = root.find("vocabularies")
        ontologies = OntologyConverter.relaxedToCompatible(ontologies)
        newRoot.append(ontologies)
        
        sentences = ET.Element("sentences")
        newRoot.append(sentences)
        for a in root.find("sentences").findall("sentence"):
            sentences.append( SentenceConverter.relaxedToCompatible(a) )

        # predicatemapping
        tmpMap = dict( [(x.attrib['relaxed_mapsTo'],x.attrib['type'])
                        for x in ontologies.getiterator("relentitytype")
                        if x.attrib.has_key("relaxed_mapsTo")] )
        for x in sentences.getiterator("relentity"):
            if x.attrib['relaxed_tag']=='entity' and \
                   tmpMap.has_key(x.attrib['type']):
                x.attrib['type'] = tmpMap[x.attrib['type']]

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)

    @classmethod
    def compatibleToOld(cls,root):
        """
        Converts 'compatible' format to 'old' format.

        @param root: root node of the corpus
        @type root: cElementTree.Element
        @return: root node of the corpus
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting corpus to compatible format..")

        newRoot = ET.Element("bioinfer")

        ontologies = root.find("vocabularies")
        ontologies = OntologyConverter.compatibleToOld(ontologies)
        for x in ontologies.findall("ontology"):
            newRoot.append(x)

        sentences = ET.Element("sentences")
        newRoot.append(sentences)
        for a in root.find("sentences").findall("sentence"):
            sentences.append( SentenceConverter.compatibleToOld(a) )
        
        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)



class SentenceConverter:
    """
    Workhorse class
    """
    @classmethod
    def oldToCompatible(cls,node,symmetrics):
        """
        Converts 'old' format to 'compatible' format.

        Note: all original attributes are first prefixed with
        'relaxed_' and then those that are in the XSD are renamed
        accordingly.

        @param node: root node in old format
        @type  node: cElementTree.Element
        @return: root node in compatible format
        @rtype: cElementTree.Element
        """
        def isSymmetric(predtype):
            return(predtype in symmetrics)
        
        printMessage(cls,inspect.stack()[0][3],
                     "Converting sentence (%s) to compatible format.."%
                     node.attrib['id'])
        node = copy.deepcopy(node)

        newNode = ET.Element("sentence",**node.attrib)
        for a in newNode.attrib.keys():
            newNode.attrib['relaxed_'+a] = newNode.attrib.pop(a)
        newNode.attrib['id'] = newNode.attrib.pop('relaxed_id')
        newNode.attrib['PMID'] = newNode.attrib.pop('relaxed_PMID')
        newNode.attrib['text'] = newNode.attrib.pop('relaxed_origText')

        # resulting elements
        out_st = []
        out_dt = []
        out_db = []
        out_dn = []
        out_de = []
        out_rt = []
        out_rb = []
        out_rn = []
        out_re = []
        
        # generate dependencies
        oldtokenid2dn = {}
        dt_counter = Increment()
        dn_counter = Increment()
        de_counter = Increment()
    
        # generate subtokens and tokens
        for a in node.getiterator("token"):
            # create deptoken
            dt = ET.Element("deptoken",**a.attrib)
            for x in dt.attrib.keys():
                dt.attrib['relaxed_'+x] = dt.attrib.pop(x)
            dt.attrib['id'] = 'dt.%s.%s'%(node.attrib['id'],
                                          str(dt_counter.get()))
            off_s = int(dt.attrib.pop('relaxed_charOffset'))
            # create subtokens
            for b in a.findall("subtoken"):
                st = ET.Element("subtoken",**b.attrib)
                for x in st.attrib.keys():
                    st.attrib['relaxed_'+x] = st.attrib.pop(x)
                st.attrib['id'] = st.attrib.pop('relaxed_id')
                st.attrib['text'] = st.attrib.pop('relaxed_text')
                off_e = off_s + len(st.attrib['text'])
                st.attrib['offset_bgn'] = str(off_s)
                st.attrib['offset_end'] = str(off_e-1)
                off_s = off_e
                dt.append(ET.Element("nestedsubtoken",
                                     subtoken=st.attrib['id'],
                                     special='False'))
                out_st.append(st)
            out_dt.append(dt)
            # create depentity and depnode
            db = ET.Element("depentity",
                           token=dt.attrib['id'],
                           type="n/a",
                           id=dt.attrib.pop('relaxed_id'))
            dn = ET.Element("depnode",
                           entity=db.attrib['id'],
                           id='dn.%s.%s'%(node.attrib['id'],
                                          str(dn_counter.get())))
            oldtokenid2dn[db.attrib['id']] = dn
            out_db.append(db)
            out_dn.append(dn)
    
        # generate linkages
        for a in node.find("linkages").findall("linkage"):
            typ = a.attrib['type']
            # NOTE: here we lose the other attributes in 'linkage'
            for b in a.findall("link"):
                link = ET.Element("depedge",**b.attrib)
                for x in link.attrib.keys():
                    link.attrib['relaxed_'+x] = link.attrib.pop(x)
                link.attrib['id'] = 'de.%s.%s'%(node.attrib['id'],
                                                str(de_counter.get()))
                link.attrib['linkage'] = typ
                link.attrib['category'] = link.attrib.pop('relaxed_category')
                link.attrib['type'] = link.attrib.pop('relaxed_type')
                uid1 = link.attrib.pop('relaxed_token1')
                uid2 = link.attrib.pop('relaxed_token2')
                link.attrib['bgn'] = oldtokenid2dn[uid1].attrib['id']
                link.attrib['end'] = oldtokenid2dn[uid2].attrib['id']
                link.attrib['status'] = link.attrib.pop('relaxed_status')
                out_de.append(link)

        # generate interactions
        rtUsed = {}
        rbcounts = {}
        entitiesLeft = {}
        rbid2rn = {}
        rt_counter = Increment()
        rn_counter = Increment()
        re_counter = Increment()
        nonphys_counter = Increment()

        # create an empty reltoken for anonymous and alike
        emptyToken = ET.Element("reltoken",
                                id="emptytoken")
        uniStr = ET.tostring(ET.Element("tmp"))
        rtUsed[uniStr] = emptyToken
        out_rt.append(emptyToken)

        # generate entity reltokens
        # (collect "true" entities)
        for a in node.getiterator("entity"):
            # create reltoken for all entities
            tmp = ET.Element("tmp")
            for x in a.findall("nestedsubtoken"):
                tmp.append(x)
            uniStr = ET.tostring(tmp)
            # if subtoken group (uniquely identified by uniStr)
            # is encountered before, use existing reltoken
            # else create a new reltoken
            if not rtUsed.has_key(uniStr):
                rt = ET.Element("reltoken",
                                id='rt.%s.%s'%(node.attrib['id'],
                                               str(rt_counter.get())))
                for c in a.findall("nestedsubtoken"):
                    st = ET.Element("nestedsubtoken",**c.attrib)
                    for x in st.attrib.keys():
                        st.attrib['relaxed_'+x] = st.attrib.pop(x)
                    st.attrib['subtoken'] = st.attrib.pop('relaxed_id')
                    st.attrib['special'] = st.attrib.pop('relaxed_special')
                    rt.append(st)
                rtUsed[uniStr] = rt
                out_rt.append(rt)
            else:
                rt = rtUsed[uniStr]

            # create relentity and relnode for "true" entities
            if not a.attrib['type']=="RELATIONSHIP_TEXTBINDING":
                # create relentity
                rb = ET.Element("relentity",**a.attrib)
                for x in rb.attrib.keys():
                    rb.attrib['relaxed_'+x] = rb.attrib.pop(x)
                rb.attrib['id'] = rb.attrib.pop('relaxed_id')
                rb.attrib['relaxed_tag'] = "entity"
                rb.attrib['token'] = rt.attrib['id']
                rb.attrib['type'] = rb.attrib.pop('relaxed_type')
                rb.attrib['isName'] = rb.attrib.pop('relaxed_isName')
                rb.attrib['meta_annotation'] = rb.attrib.pop('relaxed_annotation')
                uniStr = "%s/%s"%(rb.attrib['type'],rb.attrib['token'])
                if not rbcounts.has_key(uniStr):
                    rbcounts[uniStr] = 0
                else:
                    rbcounts[uniStr] += 1
                rb.attrib['semanticId'] = str(rbcounts[uniStr])

                # create relnode
                rn = ET.Element("relnode",
                                entity=rb.attrib['id'],
                                id='rn.%s.%s'%(node.attrib['id'],
                                               str(rn_counter.get())))
                rbid2rn[rb.attrib['id']] = rn
                out_rb.append(rb)
                out_rn.append(rn)
            else:
                entitiesLeft[a.attrib['id']] = (a,rt)

        # generate nesting reledges
        # (collect edge information from 'entitynesting' nodes)
        for a in node.findall("entitynesting"):
            re = ET.Element("reledge",**a.attrib)
            for x in re.attrib.keys():
                re.attrib['relaxed_'+x] = re.attrib.pop(x)
            re.attrib['id'] = 're.%s.%s'%(node.attrib['id'],
                                          str(re_counter.get()))
            re.attrib['type'] = "nesting"
            outer = re.attrib.pop('relaxed_outerid')
            inner = re.attrib.pop('relaxed_innerid')
            re.attrib['bgn'] = rbid2rn[outer].attrib['id']
            re.attrib['end'] = rbid2rn[inner].attrib['id']
            out_re.append(re)

        # process relnodes into nodes&edges
        # collect relationship entities
        # collect edge information from 'relnode' nodes
        def processRelnode(relnode):
            # create new relentity and new relnode for all relnodes
            if 'entity' in relnode.keys():
                oldEntity,newToken = entitiesLeft[relnode.attrib['entity']]
                # create relentity
                rb = ET.Element("relentity",**oldEntity.attrib)
                for x in rb.attrib.keys():
                    rb.attrib['relaxed_'+x] = rb.attrib.pop(x)
                del rb.attrib['relaxed_type'] # this is always RELATIONSHIP_TEXTBINDING
                rb.attrib['relaxed_tag'] = "relnode"
                rb.attrib['id']="%s.%s"%(rb.attrib.pop('relaxed_id'),
                                         nonphys_counter.get())
                rb.attrib['token'] = newToken.attrib['id']
                rb.attrib['type'] = relnode.attrib['predicate']
                rb.attrib['isName'] = rb.attrib.pop('relaxed_isName')
                rb.attrib['meta_annotation'] = rb.attrib.pop('relaxed_annotation')
                uniStr = "%s/%s"%(rb.attrib['type'],rb.attrib['token'])
                if not rbcounts.has_key(uniStr):
                    rbcounts[uniStr] = 0
                else:
                    rbcounts[uniStr] += 1
                rb.attrib['semanticId'] = str(rbcounts[uniStr])
                # create relnode
                rn = ET.Element("relnode",**relnode.attrib)
                del rn.attrib['predicate']
                del rn.attrib['entity']
                for x in rn.attrib.keys():
                    rn.attrib['relaxed_'+x] = rn.attrib.pop(x)
                rn.attrib['id'] = 'rn.%s.%s'%(node.attrib['id'],
                                              str(rn_counter.get()))
                rn.attrib['entity'] = rb.attrib['id']
                out_rb.append(rb)
                out_rn.append(rn)
            else:
                # create relentity
                rb = ET.Element("relentity")
                rb.attrib['relaxed_tag'] = "relnode"
                rb.attrib['id']='anon.%s.%s'%(node.attrib['id'],
                                              nonphys_counter.get())
                rb.attrib['meta_annotation']='n/a'
                rb.attrib['relaxed_other']='n/a'
                rb.attrib['token'] = emptyToken.attrib['id']
                rb.attrib['type'] = relnode.attrib['predicate']
                rb.attrib['isName'] = 'False'

                uniStr = "%s/%s"%(rb.attrib['type'],rb.attrib['token'])
                if not rbcounts.has_key(uniStr):
                    rbcounts[uniStr] = 0
                else:
                    rbcounts[uniStr] += 1
                rb.attrib['semanticId'] = str(rbcounts[uniStr])
                # create relnode
                rn = ET.Element("relnode",**relnode.attrib)
                del rn.attrib['predicate']
                for x in rn.attrib.keys():
                    rn.attrib['relaxed_'+x] = rn.attrib.pop(x)
                rn.attrib['id'] = 'rn.%s.%s'%(node.attrib['id'],
                                              str(rn_counter.get()))
                rn.attrib['entity'] = rb.attrib['id']
                out_rb.append(rb)
                out_rn.append(rn)

            # process children
            ends = []
            for a in relnode[:]:
                if a.tag=="relnode":
                    ends.append( processRelnode(a) )
                else: # entitynode
                    ends.append( rbid2rn[a.attrib['entity']] )

            # process edges
            if isSymmetric(relnode.attrib['predicate']):
                # NOTE:
                # if len(ends)==1, then self-interaction
                # in which case we lose the 'self'-part of the interaction
                # possible solutions:
                #  - assign 'self' instead of 'agpat'
                #  - make to identical edges (which is currently prohibited)
                for tmp in ends:
                    x = ET.Element("reledge",
                                   type="agpat",
                                   bgn=rn.attrib['id'],
                                   end=tmp.attrib['id'],
                                   id='re.%s.%s'%(node.attrib['id'],
                                                  str(re_counter.get())))
                    out_re.append(x)
            else:
                if len(ends)==1:
                    tmp1 = ends[0]
                    tmp2 = ends[0]
                elif len(ends)==2:
                    tmp1 = ends[0]
                    tmp2 = ends[1]
                else:
                    printError(cls,inspect.stack()[0][3],
                               "Invalid number of arguments in an asymmetric predicate")
                x = ET.Element("reledge",
                               type="agent",
                               bgn=rn.attrib['id'],
                               end=tmp1.attrib['id'],
                               id='re.%s.%s'%(node.attrib['id'],
                                              str(re_counter.get())))
                out_re.append(x)
                x = ET.Element("reledge",
                               type="patient",
                               bgn=rn.attrib['id'],
                               end=tmp2.attrib['id'],
                               id='re.%s.%s'%(node.attrib['id'],
                                              str(re_counter.get())))
                out_re.append(x)
            return(rn)

        for a in node.find("formulas").findall("formula"):
            for b in a.findall("relnode"):
                processRelnode(b)

        tmp = ET.Element("subtokens")
        newNode.append(tmp)
        for a in out_st:
            tmp.append(a)

        tmp = ET.Element("depannotation")
        newNode.append(tmp)
        for a in out_dt:
            tmp.append(a)
        for a in out_db:
            tmp.append(a)
        for a in out_dn:
            tmp.append(a)
        for a in out_de:
            tmp.append(a)
            
        tmp = ET.Element("relannotation")
        newNode.append(tmp)
        for a in out_rt:
            tmp.append(a)
        for a in out_rb:
            tmp.append(a)
        for a in out_rn:
            tmp.append(a)
        for a in out_re:
            tmp.append(a)

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newNode)

    @classmethod
    def compatibleToRelaxed(cls,node,physicals):
        """
        Converts 'compatible' format to 'relaxed' format.

        @param node: root node in compatible format
        @type  node: cElementTree.Element
        @return: root node in relaxed format
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting sentence (%s) to relaxed format.."%
                     node.attrib['id'])
        node = copy.deepcopy(node)

        # unify duplicate relentities
        #  - apply to processes and properties

        def mapId(old,new):
            if idmap.has_key(old):
                printError(cls,inspect.stack()[0][3],
                           "Duplicate id: %s"%old)
            idmap[old] = new

        idmap = {}
        str2rbid = {}

        st_counter = Increment()
        for st in node.find("subtokens").findall("subtoken"):
            mapId(st.attrib['id'],
                  'st.%s.%s'%(node.attrib['id'],str(st_counter.get())))

        dt_counter = Increment()
        db_counter = Increment()
        dn_counter = Increment()
        de_counter = Increment()

        for dt in node.find("depannotation").findall("deptoken"):
            mapId(dt.attrib['id'],
                  'dt.%s.%s'%(node.attrib['id'],str(dt_counter.get())))

        for db in node.find("depannotation").findall("depentity"):
            mapId(db.attrib['id'],
                  'db.%s.%s'%(node.attrib['id'],str(db_counter.get())))

        for dn in node.find("depannotation").findall("depnode"):
            mapId(dn.attrib['id'],
                  'dn.%s.%s'%(node.attrib['id'],str(dn_counter.get())))

        for de in node.find("depannotation").findall("depedge"):
            mapId(de.attrib['id'],
                  'de.%s.%s'%(node.attrib['id'],str(de_counter.get())))

        rt_counter = Increment()
        rb_counter = Increment()
        rn_counter = Increment()
        re_counter = Increment()

        for rt in node.find("relannotation").findall("reltoken"):
            mapId(rt.attrib['id'],
                  'rt.%s.%s'%(node.attrib['id'],str(rt_counter.get())))

        for rb in node.find("relannotation").findall("relentity"):
            if rb.attrib['type'] in physicals:
                # physical entities are mapped directly
                mapId(rb.attrib['id'],
                      'rb.%s.%s'%(node.attrib['id'],str(rb_counter.get())))
            else:
                # abstract entities are joined when possible
                tmp = copy.deepcopy(rb)
                del tmp.attrib['semanticId']
                del tmp.attrib['id']
                uniStr = ET.tostring(tmp)
                if not str2rbid.has_key(uniStr):
                    str2rbid[uniStr] = []
                str2rbid[uniStr].append(rb)
        # map duplicates into a single entity and remove others
        parent = node.find("relannotation")
        for x in str2rbid.values():
            rb = x.pop(0)
            newId = 'rb.%s.%s'%(node.attrib['id'],str(rb_counter.get()))
            mapId(rb.attrib['id'],newId)
            for rb in x:
                mapId(rb.attrib['id'],newId)
                parent.remove(rb)

        for rn in node.find("relannotation").findall("relnode"):
            mapId(rn.attrib['id'],
                  'rn.%s.%s'%(node.attrib['id'],str(rn_counter.get())))

        for re in node.find("relannotation").findall("reledge"):
            mapId(re.attrib['id'],
                  're.%s.%s'%(node.attrib['id'],str(re_counter.get())))

        for x in node.getiterator():
            for k,v in x.attrib.items():
                if idmap.has_key(v):
                    x.attrib[k] = idmap[v]

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(node)

    @classmethod
    def relaxedToCompatible(cls,node):
        printMessage(cls,inspect.stack()[0][3],
                     "Converting sentence (%s) to compatible format.."%
                     node.attrib['id'])
        node = copy.deepcopy(node)
        # NOTE: it is not verified that
        #       interactions are expressable w/ predicates
        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(node)

    @classmethod
    def compatibleToOld(cls,node):
        """
        Converts 'compatible' format to 'old' format.

        @param node: root node in compatible format
        @type  node: cElementTree.Element
        @return: root node in old format
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting sentence (%s) to old format.."%
                     node.attrib['id'])

        newNode = ET.Element("sentence",**node.attrib)
        newNode.attrib['origText'] = newNode.attrib.pop('text')
        for x in newNode.attrib.keys():
            if x.startswith('relaxed_'):
                newNode.attrib[x.partition('_')[2]] = newNode.attrib.pop(x)
        
        out_token = []
        out_entity = []
        out_nesting = []
        out_linkage = {}
        out_formula = []
        
        id2st = {}
        st2st = {}
        id2t = {}
        stid2offset = {}
        dn2db = {}
        db2dt = {}
        for a in node.find("subtokens").findall("subtoken"):
            st = ET.Element("subtoken",**a.attrib)
            del st.attrib['offset_bgn']
            del st.attrib['offset_end']
            for x in st.attrib.keys():
                if x.startswith('relaxed_'):
                    st.attrib[x.partition('_')[2]] = st.attrib.pop(x)
            id2st[st.attrib['id']] = st
            stid2offset[a.attrib['id']] = a.attrib['offset_bgn']

        # NOTE: here we lose (non-informative) 'special' attribute
        for a in node.find("depannotation").findall("deptoken"):
            running = Increment()
            t = ET.Element("token",**a.attrib)
            t.attrib['charOffset'] = stid2offset[a[0].attrib['subtoken']]
            t.attrib['id'] = '.'.join(['t',a.attrib['id'].split('.',1)[1]])
            for x in t.attrib.keys():
                if x.startswith('relaxed_'):
                    t.attrib[x.partition('_')[2]] = t.attrib.pop(x)
            for b in a[:]:
                st = copy.deepcopy(id2st[b.attrib['subtoken']])
                st.attrib['id'] = 's'+t.attrib['id']+'.'+str(running.get())
                t.append(st)
                st2st[b.attrib['subtoken']] = st.attrib['id']
            id2t[a.attrib['id']] = t
            out_token.append(t)

        for a in node.find("depannotation").findall("depnode"):
            dn2db[a.attrib['id']] = a.attrib['entity']
        # NOTE: here we lose possible 'type' attribute
        for a in node.find("depannotation").findall("depentity"):
            db2dt[a.attrib['id']] = id2t[a.attrib['token']].attrib['id']
        
        for a in node.find("depannotation").findall("depedge"):
            linkage = a.attrib['linkage']
            if not out_linkage.has_key(linkage):
                out_linkage[linkage] = ET.Element("linkage",type=linkage)
            tmp = ET.Element("link",**a.attrib)
            del tmp.attrib['id']
            del tmp.attrib['linkage']
            tmp.attrib['token1'] = db2dt[dn2db[tmp.attrib.pop('bgn')]]
            tmp.attrib['token2'] = db2dt[dn2db[tmp.attrib.pop('end')]]
            for x in t.attrib.keys():
                if x.startswith('relaxed_'):
                    t.attrib[x.partition('_')[2]] = t.attrib.pop(x)
            out_linkage[linkage].append(tmp)

        oldrtid2rt = {}
        oldrnid2rn = {}
        oldrbid2rb = {}
        oldrbid2newe = {}
        id2newe = {}
        later = []
        
        for a in node.find("relannotation").findall("reltoken"):
            oldrtid2rt[a.attrib['id']] = a
        for a in node.find("relannotation").findall("relnode"):
            oldrnid2rn[a.attrib['id']] = a
        for a in node.find("relannotation").findall("relentity"):
            oldrbid2rb[a.attrib['id']] = a
            if a.attrib['relaxed_tag']=='entity':
                # each entity is a (biologically)  different
                # -> always new entity
                e = ET.Element("entity",**a.attrib)
                e.attrib['annotation'] = e.attrib.pop('meta_annotation')
                e.attrib['id'] = '.'.join(['e',e.attrib['id'].split('.',1)[1]])
                del e.attrib['semanticId']
                del e.attrib['relaxed_tag']
                for x in oldrtid2rt[e.attrib.pop('token')][:]:
                    tmp = ET.Element("nestedsubtoken",**x.attrib)
                    tmp.attrib['id'] = st2st[tmp.attrib.pop('subtoken')]
                    for z in tmp.attrib.keys():
                        if z.startswith('relaxed_'):
                            tmp.attrib[z.partition('_')[2]] = z.attrib.pop(tmp)
                    e.append(tmp)
                for x in e.attrib.keys():
                    if x.startswith('relaxed_'):
                        e.attrib[x.partition('_')[2]] = e.attrib.pop(x)
                out_entity.append(e)
                oldrbid2newe[a.attrib['id']] = e
                id2newe[a.attrib['id']] = e

            elif a.attrib['relaxed_tag']=='relnode':
                later.append(a.attrib)
            else:
                printError(cls,inspect.stack()[0][3],
                           "No 'relaxed_tag' in %s"%(a))

        # process relnodes
        str2id = {}
        for a in later:
            e = ET.Element("entity",**a)
            if len(oldrtid2rt[e.attrib['token']])==0:
                # no entity for null relationship textbindings
                continue
            # type (nor semanticId) does not count towards differentness
            e.attrib['annotation'] = e.attrib.pop('meta_annotation')
            e.attrib['type'] = 'RELATIONSHIP_TEXTBINDING'
            e.attrib['id'] = '.'.join(['e',e.attrib['id'].split('.',1)[1]])
            del e.attrib['semanticId']
            del e.attrib['relaxed_tag']
            for x in oldrtid2rt[e.attrib.pop('token')][:]:
                tmp = ET.Element("nestedsubtoken",**x.attrib)
                tmp.attrib['id'] = st2st[tmp.attrib.pop('subtoken')]
                for z in tmp.attrib.keys():
                    if z.startswith('relaxed_'):
                        tmp.attrib[z.partition('_')[2]] = z.attrib.pop(tmp)
                e.append(tmp)
            for x in e.attrib.keys():
                if x.startswith('relaxed_'):
                    e.attrib[x.partition('_')[2]] = e.attrib.pop(x)
            id2newe[a['id']] = e
        # find identical RELATIONSHIP_TEXTBINDING entities
        for k,v in id2newe.items():
            if v.attrib['type']=='RELATIONSHIP_TEXTBINDING':
                tmp = copy.deepcopy(v)
                del tmp.attrib['id'] # id is the only acceptable difference
                tmpstr = ET.tostring(tmp)
                if not str2id.has_key(tmpstr):
                    str2id[tmpstr] = []
                str2id[tmpstr].append(k)
        # check if there are unique prefixes
        # if yes, use the prefix instead of full ids
        str2set = dict( [ (k,set([x.rpartition('.')[0] for x in y]))
                          for k,y in str2id.items() ] )
        all = [x for y in str2set.values() for x in y]
        # map all identical entities to the first one in the list
        for k,v in str2id.items():
            for a in v:
                oldrbid2newe[a] = id2newe[v[0]]
            out_entity.append(id2newe[v[0]]) # this is the one
            tmp = str2set[k]
            if len(tmp)==1 and all.count(list(tmp)[0])==1:
                uid = id2newe[v[0]].attrib['id']
                id2newe[v[0]].attrib['id'] = uid.rpartition('.')[0]
        
        # process reledges
        for a in node.find("relannotation").findall("reledge"):
            if a.attrib['type']=='nesting':
                tmp = ET.Element("entitynesting",**a.attrib)
                del tmp.attrib['id']
                del tmp.attrib['type']
                uid1 = oldrbid2newe[oldrnid2rn[tmp.attrib.pop('bgn')].attrib['entity']]
                uid2 = oldrbid2newe[oldrnid2rn[tmp.attrib.pop('end')].attrib['entity']]
                tmp.attrib['outerid'] = uid1.attrib['id']
                tmp.attrib['innerid'] = uid2.attrib['id']
                for z in tmp.attrib.keys():
                    if z.startswith('relaxed_'):
                        tmp.attrib[z.partition('_')[2]] = z.attrib.pop(tmp)
                out_nesting.append(tmp)

        tmpG = NX.XDiGraph()
        for a in node.find("relannotation").findall("reledge"):
            tmpG.add_edge(a.attrib['bgn'],
                          a.attrib['end'],
                          a.attrib['type'])

        # does NOT check that the relationship is expressable w/ predicates
        def addRel(newNode,node,G):
            oldnode = oldrnid2rn[node]
            oldent = oldrbid2rb[oldnode.attrib['entity']]
            if oldent.attrib['relaxed_tag']=="relnode":
                tmp = ET.Element("relnode",**oldnode.attrib)
                del tmp.attrib['id']
                if oldrbid2newe.has_key(oldnode.attrib['entity']):
                    newent = oldrbid2newe[oldnode.attrib['entity']]
                    tmp.attrib['entity'] = newent.attrib['id']
                else:
                    del tmp.attrib['entity']
                tmp.attrib['predicate'] = oldent.attrib['type']
                for z in tmp.attrib.keys():
                    if z.startswith('relaxed_'):
                        tmp.attrib[z.partition('_')[2]] = z.attrib.pop(tmp)
                # just add all edges as arguments
                edges = {'self':[],'agpat':[],'agent':[],'patient':[]}
                for a in G.out_edges(node):
                    typ = a[2]
                    edges[typ].append(a[1])
                for a in edges['self']:
                    addRel(tmp,a,G)
                for a in edges['agpat']:
                    addRel(tmp,a,G)
                for a in edges['agent']:
                    addRel(tmp,a,G)
                for a in edges['patient']:
                    addRel(tmp,a,G)
            else:
                tmp = ET.Element("entitynode",**oldnode.attrib)
                del tmp.attrib['id']
                if oldrbid2newe.has_key(oldnode.attrib['entity']):
                    newent = oldrbid2newe[oldnode.attrib['entity']]
                    tmp.attrib['entity'] = newent.attrib['id']
                else:
                    del tmp.attrib['entity']
                for z in tmp.attrib.keys():
                    if z.startswith('relaxed_'):
                        tmp.attrib[z.partition('_')[2]] = z.attrib.pop(tmp)
            newNode.append(tmp)
            
        for a in tmpG.nodes():
            if not tmpG.in_edges(a) and oldrbid2rb[oldrnid2rn[a].attrib['entity']].attrib['relaxed_tag']=="relnode":
                tmp = ET.Element("formula")
                out_formula.append(tmp)
                addRel(tmp,a,tmpG)
            
        for a in out_token:
            newNode.append(a)
        for a in out_entity:
            newNode.append(a)
        for a in out_nesting:
            newNode.append(a)
        linkages = ET.Element("linkages")
        newNode.append(linkages)
        for a in out_linkage.values():
            linkages.append(a)
        formulas = ET.Element("formulas")
        newNode.append(formulas)
        for a in out_formula:
            formulas.append(a)

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newNode)



class OntologyConverter:
    """
    Workhorse class
    """
    @classmethod
    def oldToCompatible(cls,root):
        """
        Converts 'old' format to 'compatible' format.

        @param root: root node in old format
        @type  root: cElementTree.Element
        @return: root node in compatible format
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting ontologies to 'compatible' format..")

        newRoot = ET.Element("vocabularies")

        # depentityontology
        ontology = ET.Element("depentityvocabulary")
        newRoot.append(ontology)
        ontology.append(ET.Element("depentitytype",type="n/a"))


        # depedgeontology
        ontology = ET.Element("depedgevocabulary")
        newRoot.append(ontology)

        # NOTE: These three should not be allowed
        # ontology.append(ET.Element("depedgetype",type=""))
        # ontology.append(ET.Element("depedgetype",type="none"))
        # ontology.append(ET.Element("depedgetype",type="None"))
        ontology.append(ET.Element("depedgetype",type="<acomp"))
        ontology.append(ET.Element("depedgetype",type="<advcl"))
        ontology.append(ET.Element("depedgetype",type="<advmod"))
        ontology.append(ET.Element("depedgetype",type="<amod"))
        ontology.append(ET.Element("depedgetype",type="<appos"))
        ontology.append(ET.Element("depedgetype",type="<attr"))
        ontology.append(ET.Element("depedgetype",type="<cc"))
        ontology.append(ET.Element("depedgetype",type="<ccomp"))
        ontology.append(ET.Element("depedgetype",type="<conj"))
        ontology.append(ET.Element("depedgetype",type="<dep"))
        ontology.append(ET.Element("depedgetype",type="<dobj"))
        ontology.append(ET.Element("depedgetype",type="<infmod"))
        ontology.append(ET.Element("depedgetype",type="<iobj"))
        ontology.append(ET.Element("depedgetype",type="<neg"))
        ontology.append(ET.Element("depedgetype",type="<nsubj"))
        ontology.append(ET.Element("depedgetype",type="<num"))
        ontology.append(ET.Element("depedgetype",type="<number"))
        ontology.append(ET.Element("depedgetype",type="<partmod"))
        ontology.append(ET.Element("depedgetype",type="<pobj"))
        ontology.append(ET.Element("depedgetype",type="<possessive"))
        ontology.append(ET.Element("depedgetype",type="<prep"))
        ontology.append(ET.Element("depedgetype",type="<prt"))
        ontology.append(ET.Element("depedgetype",type="<rcmod"))
        ontology.append(ET.Element("depedgetype",type="<ref"))
        ontology.append(ET.Element("depedgetype",type="<xcomp"))
        ontology.append(ET.Element("depedgetype",type="advcl>"))
        ontology.append(ET.Element("depedgetype",type="advmod>"))
        ontology.append(ET.Element("depedgetype",type="amod>"))
        ontology.append(ET.Element("depedgetype",type="aux>"))
        ontology.append(ET.Element("depedgetype",type="auxpass>"))
        ontology.append(ET.Element("depedgetype",type="cc>"))
        ontology.append(ET.Element("depedgetype",type="ccomp>"))
        ontology.append(ET.Element("depedgetype",type="complm>"))
        ontology.append(ET.Element("depedgetype",type="cop>"))
        ontology.append(ET.Element("depedgetype",type="dep>"))
        ontology.append(ET.Element("depedgetype",type="det>"))
        ontology.append(ET.Element("depedgetype",type="dobj>"))
        ontology.append(ET.Element("depedgetype",type="expl>"))
        ontology.append(ET.Element("depedgetype",type="infmod>"))
        ontology.append(ET.Element("depedgetype",type="mark>"))
        ontology.append(ET.Element("depedgetype",type="neg>"))
        ontology.append(ET.Element("depedgetype",type="nmod>"))
        ontology.append(ET.Element("depedgetype",type="nsubj>"))
        ontology.append(ET.Element("depedgetype",type="nsubjpass>"))
        ontology.append(ET.Element("depedgetype",type="num>"))
        ontology.append(ET.Element("depedgetype",type="partmod>"))
        ontology.append(ET.Element("depedgetype",type="poss>"))
        ontology.append(ET.Element("depedgetype",type="preconj>"))
        ontology.append(ET.Element("depedgetype",type="predet>"))
        ontology.append(ET.Element("depedgetype",type="prep>"))
        ontology.append(ET.Element("depedgetype",type="rel>"))
        ontology.append(ET.Element("depedgetype",type="xsubj>"))
        ontology.append(ET.Element("depedgetype",type="A"))
        ontology.append(ET.Element("depedgetype",type="A/AN"))
        ontology.append(ET.Element("depedgetype",type="Ah"))
        ontology.append(ET.Element("depedgetype",type="ALx"))
        ontology.append(ET.Element("depedgetype",type="B"))
        ontology.append(ET.Element("depedgetype",type="Bp"))
        ontology.append(ET.Element("depedgetype",type="Bpj"))
        ontology.append(ET.Element("depedgetype",type="Bs"))
        ontology.append(ET.Element("depedgetype",type="Bsj"))
        ontology.append(ET.Element("depedgetype",type="Bsm"))
        ontology.append(ET.Element("depedgetype",type="Ca"))
        ontology.append(ET.Element("depedgetype",type="CC"))
        ontology.append(ET.Element("depedgetype",type="Ce"))
        ontology.append(ET.Element("depedgetype",type="Cet"))
        ontology.append(ET.Element("depedgetype",type="CO"))
        ontology.append(ET.Element("depedgetype",type="COd"))
        ontology.append(ET.Element("depedgetype",type="COORD"))
        ontology.append(ET.Element("depedgetype",type="COp"))
        ontology.append(ET.Element("depedgetype",type="CQ"))
        ontology.append(ET.Element("depedgetype",type="Cr"))
        ontology.append(ET.Element("depedgetype",type="Cs"))
        ontology.append(ET.Element("depedgetype",type="D"))
        ontology.append(ET.Element("depedgetype",type="D^c"))
        ontology.append(ET.Element("depedgetype",type="DD"))
        ontology.append(ET.Element("depedgetype",type="DG"))
        ontology.append(ET.Element("depedgetype",type="Dm"))
        ontology.append(ET.Element("depedgetype",type="Dmc"))
        ontology.append(ET.Element("depedgetype",type="Dmck"))
        ontology.append(ET.Element("depedgetype",type="Dmcm"))
        ontology.append(ET.Element("depedgetype",type="Dmcn"))
        ontology.append(ET.Element("depedgetype",type="Dmcw"))
        ontology.append(ET.Element("depedgetype",type="Dmcy"))
        ontology.append(ET.Element("depedgetype",type="Dmnc"))
        ontology.append(ET.Element("depedgetype",type="Dmu"))
        ontology.append(ET.Element("depedgetype",type="Dmum"))
        ontology.append(ET.Element("depedgetype",type="DP"))
        ontology.append(ET.Element("depedgetype",type="Ds"))
        ontology.append(ET.Element("depedgetype",type="Dsu"))
        ontology.append(ET.Element("depedgetype",type="D^u"))
        ontology.append(ET.Element("depedgetype",type="E"))
        ontology.append(ET.Element("depedgetype",type="EA"))
        ontology.append(ET.Element("depedgetype",type="EAm"))
        ontology.append(ET.Element("depedgetype",type="EAxk"))
        ontology.append(ET.Element("depedgetype",type="EAy"))
        ontology.append(ET.Element("depedgetype",type="EBm"))
        ontology.append(ET.Element("depedgetype",type="EBx"))
        ontology.append(ET.Element("depedgetype",type="Ec"))
        ontology.append(ET.Element("depedgetype",type="EC"))
        ontology.append(ET.Element("depedgetype",type="ECa"))
        ontology.append(ET.Element("depedgetype",type="ECx"))
        ontology.append(ET.Element("depedgetype",type="EE"))
        ontology.append(ET.Element("depedgetype",type="EEm"))
        ontology.append(ET.Element("depedgetype",type="EEx"))
        ontology.append(ET.Element("depedgetype",type="EI"))
        ontology.append(ET.Element("depedgetype",type="Em"))
        ontology.append(ET.Element("depedgetype",type="EN"))
        ontology.append(ET.Element("depedgetype",type="G"))
        ontology.append(ET.Element("depedgetype",type="GN"))
        ontology.append(ET.Element("depedgetype",type="H"))
        ontology.append(ET.Element("depedgetype",type="I"))
        ontology.append(ET.Element("depedgetype",type="ID"))
        ontology.append(ET.Element("depedgetype",type="If"))
        ontology.append(ET.Element("depedgetype",type="Ifd"))
        ontology.append(ET.Element("depedgetype",type="Ix"))
        ontology.append(ET.Element("depedgetype",type="J"))
        ontology.append(ET.Element("depedgetype",type="JG"))
        ontology.append(ET.Element("depedgetype",type="Jp"))
        ontology.append(ET.Element("depedgetype",type="Jr"))
        ontology.append(ET.Element("depedgetype",type="Js"))
        ontology.append(ET.Element("depedgetype",type="JT"))
        ontology.append(ET.Element("depedgetype",type="Ju"))
        ontology.append(ET.Element("depedgetype",type="Jw"))
        ontology.append(ET.Element("depedgetype",type="K"))
        ontology.append(ET.Element("depedgetype",type="L"))
        ontology.append(ET.Element("depedgetype",type="La"))
        ontology.append(ET.Element("depedgetype",type="M"))
        ontology.append(ET.Element("depedgetype",type="Ma"))
        ontology.append(ET.Element("depedgetype",type="Mam"))
        ontology.append(ET.Element("depedgetype",type="Mg"))
        ontology.append(ET.Element("depedgetype",type="MG"))
        ontology.append(ET.Element("depedgetype",type="Mgn"))
        ontology.append(ET.Element("depedgetype",type="Mgp"))
        ontology.append(ET.Element("depedgetype",type="Mj"))
        ontology.append(ET.Element("depedgetype",type="Mp"))
        ontology.append(ET.Element("depedgetype",type="Mpc"))
        ontology.append(ET.Element("depedgetype",type="Mt"))
        ontology.append(ET.Element("depedgetype",type="Mv"))
        ontology.append(ET.Element("depedgetype",type="MV"))
        ontology.append(ET.Element("depedgetype",type="MVa"))
        ontology.append(ET.Element("depedgetype",type="MVg"))
        ontology.append(ET.Element("depedgetype",type="MVi"))
        ontology.append(ET.Element("depedgetype",type="MVl"))
        ontology.append(ET.Element("depedgetype",type="Mvn"))
        ontology.append(ET.Element("depedgetype",type="MVp"))
        ontology.append(ET.Element("depedgetype",type="MVs"))
        ontology.append(ET.Element("depedgetype",type="MVt"))
        ontology.append(ET.Element("depedgetype",type="MVx"))
        ontology.append(ET.Element("depedgetype",type="MX"))
        ontology.append(ET.Element("depedgetype",type="MXp"))
        ontology.append(ET.Element("depedgetype",type="MXpa"))
        ontology.append(ET.Element("depedgetype",type="MXpd"))
        ontology.append(ET.Element("depedgetype",type="MXpp"))
        ontology.append(ET.Element("depedgetype",type="MXpr"))
        ontology.append(ET.Element("depedgetype",type="MXpx"))
        ontology.append(ET.Element("depedgetype",type="MXs"))
        ontology.append(ET.Element("depedgetype",type="MXsa"))
        ontology.append(ET.Element("depedgetype",type="MXsj"))
        ontology.append(ET.Element("depedgetype",type="MXsp"))
        ontology.append(ET.Element("depedgetype",type="MXsr"))
        ontology.append(ET.Element("depedgetype",type="MXsx"))
        ontology.append(ET.Element("depedgetype",type="N"))
        ontology.append(ET.Element("depedgetype",type="ND"))
        ontology.append(ET.Element("depedgetype",type="NI"))
        ontology.append(ET.Element("depedgetype",type="NIc"))
        ontology.append(ET.Element("depedgetype",type="NId"))
        ontology.append(ET.Element("depedgetype",type="NIf"))
        ontology.append(ET.Element("depedgetype",type="NIr"))
        ontology.append(ET.Element("depedgetype",type="NIt"))
        ontology.append(ET.Element("depedgetype",type="NM"))
        ontology.append(ET.Element("depedgetype",type="NN"))
        ontology.append(ET.Element("depedgetype",type="O"))
        ontology.append(ET.Element("depedgetype",type="O^c"))
        ontology.append(ET.Element("depedgetype",type="OF"))
        ontology.append(ET.Element("depedgetype",type="O^n"))
        ontology.append(ET.Element("depedgetype",type="Op"))
        ontology.append(ET.Element("depedgetype",type="Opc"))
        ontology.append(ET.Element("depedgetype",type="Opn"))
        ontology.append(ET.Element("depedgetype",type="Opt"))
        ontology.append(ET.Element("depedgetype",type="Os"))
        ontology.append(ET.Element("depedgetype",type="Osc"))
        ontology.append(ET.Element("depedgetype",type="Os/Js"))
        ontology.append(ET.Element("depedgetype",type="Osn"))
        ontology.append(ET.Element("depedgetype",type="Ost"))
        ontology.append(ET.Element("depedgetype",type="O^t"))
        ontology.append(ET.Element("depedgetype",type="Ox"))
        ontology.append(ET.Element("depedgetype",type="OXi"))
        ontology.append(ET.Element("depedgetype",type="Pa"))
        ontology.append(ET.Element("depedgetype",type="Paf"))
        ontology.append(ET.Element("depedgetype",type="Pafm"))
        ontology.append(ET.Element("depedgetype",type="Pam"))
        ontology.append(ET.Element("depedgetype",type="PFc"))
        ontology.append(ET.Element("depedgetype",type="PP"))
        ontology.append(ET.Element("depedgetype",type="PPf"))
        ontology.append(ET.Element("depedgetype",type="Pv"))
        ontology.append(ET.Element("depedgetype",type="Pvf"))
        ontology.append(ET.Element("depedgetype",type="QI"))
        ontology.append(ET.Element("depedgetype",type="R"))
        ontology.append(ET.Element("depedgetype",type="Rn"))
        ontology.append(ET.Element("depedgetype",type="Rnx"))
        ontology.append(ET.Element("depedgetype",type="RS"))
        ontology.append(ET.Element("depedgetype",type="RSe"))
        ontology.append(ET.Element("depedgetype",type="S"))
        ontology.append(ET.Element("depedgetype",type="S^"))
        ontology.append(ET.Element("depedgetype",type="SFp"))
        ontology.append(ET.Element("depedgetype",type="SFs"))
        ontology.append(ET.Element("depedgetype",type="SFsi"))
        ontology.append(ET.Element("depedgetype",type="SFst"))
        ontology.append(ET.Element("depedgetype",type="SIs"))
        ontology.append(ET.Element("depedgetype",type="Sp"))
        ontology.append(ET.Element("depedgetype",type="Spx"))
        ontology.append(ET.Element("depedgetype",type="Spxt"))
        ontology.append(ET.Element("depedgetype",type="Spxw"))
        ontology.append(ET.Element("depedgetype",type="Ss"))
        ontology.append(ET.Element("depedgetype",type="S^x"))
        ontology.append(ET.Element("depedgetype",type="S^xw"))
        ontology.append(ET.Element("depedgetype",type="TH"))
        ontology.append(ET.Element("depedgetype",type="THb"))
        ontology.append(ET.Element("depedgetype",type="THi"))
        ontology.append(ET.Element("depedgetype",type="TO"))
        ontology.append(ET.Element("depedgetype",type="TOf"))
        ontology.append(ET.Element("depedgetype",type="TOn"))
        ontology.append(ET.Element("depedgetype",type="TOo"))
        ontology.append(ET.Element("depedgetype",type="TOt"))
        ontology.append(ET.Element("depedgetype",type="Up"))
        ontology.append(ET.Element("depedgetype",type="Us"))
        ontology.append(ET.Element("depedgetype",type="Wd"))
        ontology.append(ET.Element("depedgetype",type="Wdc"))
        ontology.append(ET.Element("depedgetype",type="Xd"))
        ontology.append(ET.Element("depedgetype",type="YP"))
        ontology.append(ET.Element("depedgetype",type="YS"))
        ontology.append(ET.Element("depedgetype",type="Yt"))
        ontology.append(ET.Element("depedgetype",type="Ytm"))

        # relentityontology
        ontology = ET.Element("relentityvocabulary")
        newRoot.append(ontology)

        oldRel,oldEnt = root.findall("ontology")

        # one root node
        rel = copy.deepcopy(oldRel.find("reltype"))
        for b in rel.getiterator():
            b.attrib['tag'] = b.tag
            b.tag = 'relentitytype'
            for x in b.attrib.keys():
                b.attrib['relaxed_'+x] = b.attrib.pop(x)
            b.attrib['type'] = b.attrib.pop('relaxed_name')
            b.attrib['group'] = "Process"
            if b.attrib.has_key('relaxed_effect'):
                b.attrib['effect'] = b.attrib.pop('relaxed_effect')
            if b.attrib.has_key('relaxed_symmetric'):
                b.attrib['symmetric'] = b.attrib.pop('relaxed_symmetric')
        ontology.append(rel)

        def processEnt(b,cls):
            b.attrib['tag'] = b.tag
            b.tag = 'relentitytype'
            for x in b.attrib.keys():
                b.attrib['relaxed_'+x] = b.attrib.pop(x)
            b.attrib['type'] = b.attrib.pop('relaxed_name')
            b.attrib['group'] = cls
            
        # one root node
        ent = copy.deepcopy(oldEnt.find("entitytype"))
        processEnt(ent,'Other')
        idx = 0
        classes = ['Physical','Property','Process','Other']
        # the last one is for RELATIONSHIP_TEXTBINDING
        for a in ent.findall("entitytype"):
            for x in a.getiterator():
                if len(classes)>idx:
                    processEnt(x,classes[idx])
                else:
                    printError(cls,inspect.stack()[0][3],
                               "Cannot assign group to '%s'"%
                               (x.attrib['type']))
            idx += 1
        ontology.append(ent)

        # reledgeontology
        ontology = ET.Element("reledgevocabulary")
        newRoot.append(ontology)
        # NOTE: should 'nesting' be disallowed?
        ontology.append(ET.Element("reledgetype",type="nesting"))
        ontology.append(ET.Element("reledgetype",type="agent"))
        ontology.append(ET.Element("reledgetype",type="patient"))
        ontology.append(ET.Element("reledgetype",type="agpat"))
        ontology.append(ET.Element("reledgetype",type="possessor"))
        ontology.append(ET.Element("reledgetype",type="identity"))
        ontology.append(ET.Element("reledgetype",type="sub"))
        ontology.append(ET.Element("reledgetype",type="super"))
        ontology.append(ET.Element("reledgetype",type="polarity"))

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)

    @classmethod
    def compatibleToRelaxed(cls,root):
        """
        Converts 'compatible' format to 'relaxed' format.

        @param root: root node in compatible format
        @type  root: cElementTree.Element
        @return: root node in relaxed format
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting ontologies to 'relaxed' format..")
        root = copy.deepcopy(root)

        ontology = root.find("relentityvocabulary")
        rel,ent = ontology.findall("relentitytype")
        ontology.remove(ent)
        tmpMap = dict( [(x.attrib['type'],x) for x in rel.getiterator()] )

        # assumes 'mapsTo' subtree(s) are complete
        for a in ent.findall("relentitytype"):
            if a.attrib.has_key('relaxed_mapsTo'):
                for x in a.getiterator():
                    if not x.attrib.has_key('relaxed_mapsTo'):
                        printMessage(cls,inspect.stack()[0][3],
                                     "No 'relaxed_mapsTo' in %s"%
                                     (x.attrib['type']))
                        continue
                    tgt = x.attrib['relaxed_mapsTo']
                    tmpMap[tgt].attrib['relaxed_mapsTo'] = x.attrib['type']
            elif a.attrib['type']=="RELATIONSHIP_TEXTBINDING":
                pass
            else:
                ontology.append(a)

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(root)

    @classmethod
    def relaxedToCompatible(cls,root):
        """
        Converts 'relaxed' format to 'compatible' format.

        @param root: root node in relaxed format
        @type  root: cElementTree.Element
        @return: root node in compatible format
        @rtype: cElementTree.Element
        """
        def processEnt(x,ent):
            if not x.attrib.has_key('relaxed_mapsTo'):
                printMessage(cls,inspect.stack()[0][3],
                             "No 'relaxed_mapsTo' in %s"%x.attrib['type'])
                x.attrib['relaxed_mapsTo'] = ''
            tmp = ET.Element("relentitytype",
                             type=x.attrib['relaxed_mapsTo'],
                             relaxed_mapsTo=x.attrib['type'],
                             relaxed_tag="entitytype",
                             group="Process")
            del x.attrib['relaxed_mapsTo']
            ent.append(tmp)
            for a in x[:]:
                processEnt(a,x)
                
        printMessage(cls,inspect.stack()[0][3],
                     "Converting ontologies to 'compatible' format..")
        root = copy.deepcopy(root)

        ontology = root.find("relentityvocabulary")
        nodes = ontology.findall("relentitytype")
        ent = ET.Element("relentitytype",
                         type="Entity",
                         relaxed_tag="entitytype",
                         group="Other")
        for x in nodes[1:]: # the first is relationship tree and remains as is
            ent.append(x)
            ontology.remove(x)
        # assumes 'mapsTo' subtree(s) are complete
        for x in nodes[0].findall("relentitytype"):
            if x.attrib.has_key('relaxed_mapsTo'):
                processEnt(x,ent)
        ent.append(ET.Element("relentitytype",
                              type="RELATIONSHIP_TEXTBINDING",
                              relaxed_tag="entitytype",
                              group="Other"))
        ontology.append(ent)
        
        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(root)
    
    @classmethod
    def compatibleToOld(cls,root):
        """
        Converts 'new' format to 'old' format.

        @param root: root node in new format
        @type  root: cElementTree.Element
        @return: root node in old format
        @rtype: cElementTree.Element
        """
        printMessage(cls,inspect.stack()[0][3],
                     "Converting ontologies to 'old' format..")

        rel,ent = root.find("relentityvocabulary").findall("relentitytype")
        tmpRoot = None

        newRoot = ET.Element("tmp")
        newRel = ET.Element("ontology")
        newRel.attrib['type'] = "Relationship"
        newEnt = ET.Element("ontology")
        newEnt.attrib['type'] = "Entity"
        newRoot.append(newRel)
        newRoot.append(newEnt)

        tmp = copy.deepcopy(rel)
        for a in tmp.getiterator():
            a.tag = a.attrib.pop('relaxed_tag')
            a.attrib['name'] = a.attrib.pop('type')
            del a.attrib['group']
            for x in a.attrib.keys():
                if x.startswith('relaxed_'):
                    a.attrib[x.partition('_')[2]] = a.attrib.pop(x)
        newRel.append(tmp)

        tmp = copy.deepcopy(ent)
        for a in tmp.getiterator():
            a.tag = a.attrib.pop('relaxed_tag')
            a.attrib['name'] = a.attrib.pop('type')
            del a.attrib['group']
            for x in a.attrib.keys():
                if x.startswith('relaxed_'):
                    a.attrib[x.partition('_')[2]] = a.attrib.pop(x)
        newEnt.append(tmp)

        printMessage(cls,inspect.stack()[0][3],
                     "Converted")
        return(newRoot)
