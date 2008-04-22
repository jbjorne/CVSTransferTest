import time
import signal
import re
import sys
import os
import copy
import inspect
import subprocess as SP
import networkx as NX
from BIGraph import *
from BIGraph.refiners import *
import BIGraph.core.sentence as S
import BIGraph.binariser.convertrule as C

class Binariser(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        Binariser.resolveSentence(self.sentence,
                                  self.ontologies)

    def remove(self):
        self.pe("remove-method not supported",self.sentence.id)
    
    @classmethod
    def getPairs(cls,G):
        pairGs = Binariser.generatePairs(G)
        return( Binariser.prefilter(pairGs) )
    
    @classmethod
    def resolveSentence(cls,sentence,ontologies,
                        rulefile=None,pack=False,timeout=10):
        def toLines(Gs):
            lines = set()
            for counter,G in enumerate(Gs):
                lines.update( PrologConverter.toProlog(G,counter) )
            return( sorted(list(lines)) )

        ontology = ontologies['relentityvocabulary']
        in_Gs_filtered = Binariser.getPairs(sentence.interactions)
        process = Binariser.initialiseProlog(ontology,rulefile)
        if process:
            in_lines = toLines(in_Gs_filtered)
            out_lines_out,out_lines_err = Binariser.runProlog(process,
                                                              in_lines,
                                                              timeout)
            if not out_lines_out:
                printWarning(cls,
                             inspect.stack()[0][3],
                             "no Prolog output")
            Binariser.createStatistics(out_lines_out,
                                       in_Gs_filtered,
                                       sentence.interactions)
            Binariser.updateSentence(sentence,out_lines_out,pack)

    @classmethod
    def initialiseProlog(cls,ontology,rulefile):
        curdir = os.path.dirname(globals()['__file__'])
        if not rulefile:
            rulefile = "%s/rules"%curdir
        process = SP.Popen(['prolog',
                            '--quiet',
                            '-g', 'true'],
                            stderr=SP.PIPE,
                            stdout=SP.PIPE,
                            stdin=SP.PIPE)
        # consult core file
        process.stdin.write("consult('%s/core.prolog').\n"%curdir)
        # consult matching file
        process.stdin.write("consult('%s/matching.prolog').\n"%curdir)
        # consult ontology structure
        for a in ontology.id2node.values():
            for b in a.children:
                process.stdin.write("assert(parent_child('%s','%s')).\n"%
                                    (a.type,b.type))
            if not a.symmetric==None:
                process.stdin.write("assert(symmetric('%s')).\n"%
                                    (a.type))
            if not a.effect==None:
                process.stdin.write("assert(process_effect('%s','%s')).\n"%
                                    (a.type,a.effect))
            if not a.group==None:
                process.stdin.write("assert(tripletype('%s','%s')).\n"%
                                    (a.type,a.group))
        # consult rules
        try:
            tmp = open(rulefile,'r')
        except IOError, e:
            printError(cls,
                       inspect.stack()[0][3],
                       "Cannot binarise - failed to open '%s': %s"%
                       (e.filename, e.strerror) )
            return(None)
        # Prolog doesn't want \n until the whole command ends
        process.stdin.write(''.join(C.parse(tmp.read())) )
        return(process)

    @classmethod
    def runProlog(cls,process,lines,timeout):
        # write the assertions
        for b in lines:
            process.stdin.write(b)
            #sys.stderr.write("%s"%b)
        # analyse
        process.stdin.write("transform.\n")
        process.stdin.write("halt.\n")
        idx = 0
        while idx<timeout and process.poll()==None:
            interval = 0.01
            time.sleep(interval)
            idx += interval
        if process.poll()==None:
            os.kill(process.pid,signal.SIGTERM)
            sys.stderr.write("".join(process.stderr.readlines()))
            sys.stderr.write("".join(process.stdout.readlines()))
            printError(cls,
                       inspect.stack()[0][3],
                       "Cannot binarise - Prolog timed out")
            return( ([],[]) )
        if not process.poll()==0:
            sys.stderr.write("".join(process.stderr.readlines()))
            sys.stderr.write("".join(process.stdout.readlines()))
            printError(cls,
                       inspect.stack()[0][3],
                       "Cannot binarise - Error in Prolog")
            return( ([],[]) )

        pout = process.stdout.readlines()
        perr = process.stderr.readlines()
        #sys.stderr.write("".join(perr))
        #sys.stderr.write("".join(pout))
        for x in pout:
            printMessage(cls,
                         inspect.stack()[0][3],
                         "Prolog output: %s"%x.strip())
        return( (pout,perr) )

    @classmethod
    def createStatistics(cls,lines,Gs,G):
        # (pairIds are concatenated ids of the leaf (name) nodes)
        keys = sorted([x.entity.id for x in G.nodes()
                 if not G.out_edges(x) and not x.entity.type=='NOT'])
        pairs = {}
        while keys:
            current = keys.pop(0)
            for next in keys:
                pairs["%s&%s"%(current,next)] = set()

        # create keys also for those graphs
        # that did not generate any interactions
        # (graphIds are indices of the original list of pair-wise graphs)
        graphs = {}
        for key in range(len(Gs)):
            graphs[key] = set()

        for line in lines:
            tmp = PrologConverter.reOutput.search(line.strip())
            if tmp:
                runId,graphId,pairId,levelId,text = tmp.groups()
                runId,graphId,levelId = int(runId),int(graphId),int(levelId)
                pairs[pairId].add(runId)
                graphs[graphId].add(runId)

        def sortfunc(x,y):
            diff = len(y[1])-len(x[1])
            if not diff==0:
                return(diff)
            return(cmp(x[0],y[0]))

        # create statistics
        for p,rset in sorted(pairs.items(),sortfunc):
            printMessage(cls,
                         inspect.stack()[1][3],
                         "Pair %s --> %s binary interactions"
                         %(p,len(rset))
                         )
        matches = [k for k,v in graphs.items() if v]
        mismatches = [k for k,v in graphs.items() if not v]
        printMessage(cls,
                     inspect.stack()[1][3],
                     "Matched graphs = %s"%(str(matches))
                     )
        printMessage(cls,
                     inspect.stack()[1][3],
                     "Mismatched graphs = %s"%(str(mismatches))
                     )

    @classmethod
    def updateSentence(cls,sentence,lines,pack):
        Gs = PrologConverter.fromProlog(lines,
                                        sentence.id,
                                        sentence.reltokens)
        
        # remove existing interactions (preserve name nodes)
        # and create union of binary interactions
        G = sentence.interactions
        for a in G.nodes():
            if not a.entity.isName:
                G.delete_node(a)
        G.delete_edges_from(G.edges())
        for G in Gs.values():
            sentence.interactions = NX.union(sentence.interactions,G)
            if pack:
                printError(cls,
                           inspect.stack()[0][3],
                           "pack-method disabled")

        # fix reltokens and relentities
        # pick the old tokens/entities where possible
        G = sentence.interactions
        counter = Increment()

        uni2token = dict( [(x.getUniStr(),x)
                           for x in sentence.reltokens.values()] )
        sentence.reltokens = {}
        for node in G.nodes():
            uniTok = node.entity.token.getUniStr()
            if uni2token.has_key(uniTok):
                node.entity.token = uni2token[uniTok]
            else:
                uni2token[uniTok] = node.entity.token
            token = node.entity.token
            if not sentence.reltokens.has_key(token.id):
                sentence.reltokens[token.id] = token
            elif not sentence.reltokens[token.id].getUniStr() == \
                     token.getUniStr():
                sentence.setFreeId(token)
                sentence.reltokens[token.id] = token
            else:
                assert(token==sentence.reltokens[token.id])

        uni2entity = dict( [(x.getUniStr(),x)
                            for x in sentence.relentities.values()] )
        sentence.relentities = {}
        for node in G.nodes():
            uniEnt = node.entity.getUniStr()
            if uni2entity.has_key(uniEnt):
                node.entity = uni2entity[uniEnt]
            else:
                uni2entity[uniEnt] = node.entity
            entity = node.entity
            if not sentence.relentities.has_key(entity.id):
                sentence.relentities[entity.id] = entity
            elif not sentence.relentities[entity.id].getUniStr() == \
                     entity.getUniStr():
                sentence.setFreeId(entity)
                sentence.relentities[entity.id] = entity
            else:
                assert(entity==sentence.relentities[entity.id])
            # fill the missing attributes for relentities
            if not entity.__dict__.has_key('relaxed_other'):
                entity.relaxed_other = False
            if not entity.__dict__.has_key('relaxed_tag'):
                # all new entities must be relnodes in the old format
                # because old format entities are all names
                entity.relaxed_tag = 'relnode'
            if not entity.__dict__.has_key('isName'):
                entity.isName = False

        for node in G.nodes():
            node.id = 'rn.%s.%s'%(sentence.id,counter.get())

        # remove exact duplicates
        roots = [x for x in G.nodes() if not G.in_edges(x)]
        uniqs = set()
        remains = set()
        for root in roots:
            uniStr = root.entity.id
            uniStr += '/'.join(sorted(['%s/%s'%(b.entity.id,c.type)
                                       for (a,b,c) in G.out_edges(root)]))
            if not uniStr in uniqs:
                uniqs.add(uniStr)
                remains.add(root)
                for leaf in G.out_edges(root):
                    remains.add(leaf[1])
        G.subgraph(remains,inplace=True)

        # by definition of binary,
        # leafs nodes are mergeable if the entities are the same
        leafs = [x for x in G.nodes() if not G.out_edges(x)]
        e2n = {}
        for leaf in leafs:
            entity = leaf.entity
            if not e2n.has_key(entity):
                e2n[entity] = leaf
            else:
                for root,x,edge in G.in_edges(leaf):
                    G.delete_edge(root,x,edge)
                    G.add_edge(root,e2n[entity],edge)
                    edge.end = e2n[entity]
                G.delete_node(leaf)
        
        if pack:
            printError(cls,
                       inspect.stack()[0][3],
                       "pack-method disabled")
    
    @classmethod
    def generatePairs(cls,G):
        def formPaths(root):
            if not succ.has_key(root):
                return([[root]])
            return( [[root]+x for v in succ[root] for x in formPaths(v)] )

        def pathToGs(path):
            result = [NX.XDiGraph(multiedges=True)]
            idx = 1
            while idx<len(path):
                etype = G.get_edge(path[idx-1],path[idx])
                if len(etype)>1:
                    printWarning(cls,
                                 inspect.stack()[0][3],
                                 "Multiple edges from %s to %s"%
                                 (path[idx-1].id,path[idx].id))
                tmp = []
                for x in range(len(etype)):
                    edge = ( path[idx-1],
                             path[idx],
                             etype[x] )
                    tmp2 = [g.copy() for g in result]
                    for g in tmp2:
                        g.add_edge(edge)
                    tmp.extend(tmp2)
                idx += 1
                result = tmp

            nodelist = path[:]
            while nodelist:
                # NOTs are in 'polarity' format
                following = []
                for y in nodelist:
                    for x in G.out_edges(y):
                        if x[1].entity.type=='NOT' and not x[1] in path:
                            for g in result:
                                g.add_edge(x)
                            following.append(x[1])
                nodelist = following
            return(result)
            
        pairGs = []
        for a in G.nodes():
            pred,succ = Binariser.neighbors(G,a)
            paths = formPaths(a)
            halfGs = map(pathToGs,paths)
            idx1 = 0
            while idx1<len(halfGs):
                idx2 = 0
                while idx2<idx1:
                    for g1 in halfGs[idx1]:
                        for g2 in halfGs[idx2]:
                            tmp = NX.union(copy.deepcopy(g1),
                                           copy.deepcopy(g2))
                            roots = [x for x in tmp.nodes()
                                     if not tmp.in_edges(x)]
                            for d in tmp.out_edges(roots[0]):
                                # only one NOT preserved in root
                                if d[1].entity.type=='NOT':
                                    tmp.delete_node(d[1])
                                else:
                                    tmp.delete_edge(d)
                                    tmp.add_edge((roots[1],d[1],d[2]))
                            tmp.delete_node(roots[0])
                            pairGs.append(tmp)
                    idx2 += 1
                idx1 += 1
        return(pairGs)

    @classmethod
    def prefilter(cls,Gs):
        def hasValidLeafs(G):
            # here leafs are non-NOTs
            leafs = [x for x in G.nodes()
                     if not G.out_edges(x) and not x.entity.type=='NOT']
            # there must be exactly two leafs
            if not len(leafs)==2:
                #print "not exactly two leafs"
                return(False)
            # the two leafs must be names
            for x in leafs:
                if not x.entity.isName:
                    #print "non-name leaf"
                    return(False)
            # leafs must be distinct
            if leafs[0].entity.getUniStr()==leafs[1].entity.getUniStr():
                #print "only one unique leaf"
                return(False)
            return(True)
            
        def hasUniqueEdges(G):
            elist = map(lambda a: (a[0].id,
                                   a[1].id,
                                   a[2].type), G.edges())
            eset = set(elist)
            return( len(elist)==len(eset) )

        def process(function):
            current = 0
            while current<len(result):
                if function(result[current]):
                    current += 1
                else:
                    result.pop(current)

        result = Gs[:]
        process(hasValidLeafs)
        process(hasUniqueEdges)
        return(result)
    
    # adapted from NX.path.predecessor
    @classmethod
    def neighbors(cls,G,source):
        nextlevel=[source] # list of nodes to check at next level
        pred={source:set()} # predecessor dictionary
        succ={source:set()} # successor dictionary
        while nextlevel:
            thislevel=nextlevel
            nextlevel=[]
            for v in thislevel:
                for w in G.out_neighbors(v):
                    if not pred.has_key(w):
                        pred[w] = set()
                    if not succ.has_key(v):
                        succ[v] = set()
                    pred[w].add(v)
                    succ[v].add(w)
                    nextlevel.append(w)
        return (pred,succ)




class PrologConverter:
    # does not preserve node/edge ids

#    counter = 0

    # runningId : originalId : pairId : level : .*
    reOutput = re.compile(r'^(.*?):(.*?):(.*?):(.*?):(.*)$')
    reText = re.compile(r'^(.*?)\((.*)\)$')
    reNodeArgs = re.compile(r'(.*),(.*),(.*),(.*)')
    reEdgeArgs = re.compile(r'(.*),(.*),(.*)')

    @classmethod
    def toProlog(cls,G,graphId):
        counter = Increment()
        nodes = {}
        lines = set()
        for a in G.nodes():
            runId = counter.get()
            lines.add("assert(temp:node(%s,%s,%s,'%s','%s',%s)).\n"
                      %(0,
                        graphId,
                        runId,
                        a.entity.id,
                        a.entity.type,
                        "['%s']"%(a.entity.token.id))
                      )
            nodes[a] = runId
        for a in G.edges():
            lines.add("assert(temp:edge(%s,%s,%s,%s,'%s')).\n"
                      %(0,
                        graphId,
                        nodes[a[0]],
                        nodes[a[1]],
                        a[2].type
                        )
                      )
        return(lines)

    @classmethod
    def fromProlog(cls,lines,uid,origTokens):
        result = {}
        node_map = {}
        empty = {}
        for line in lines:
            tmp = PrologConverter.reOutput.search(line.strip())
            if tmp:
                runIdB,graphId,pairId,levelId,text = tmp.groups()
                if not result.has_key(runIdB):
                    result[runIdB] = NX.XDiGraph(multiedges=True)
                    node_map[runIdB] = {}
                    empty[runIdB] = S.Sentence()
                    empty[runIdB].id = uid
                    
                tmp2 = PrologConverter.reText.search(text)
                if tmp2:
                    pred,args = tmp2.groups()
                    if pred=='node':
                        tmp3 = PrologConverter.reNodeArgs.search(args)
                        if tmp3:
                            runId,entityId,eType,tokens = tmp3.groups()
                            tokens = sorted(tokens.split('-'))
                            token = empty[runIdB].newElement(S.RelToken)
                            for x in tokens:
                                # add here option to add/remove subtokens
                                for y in origTokens[x].getNested():
                                    special = (y.id in origTokens[x].special)
                                    token.addSubtoken(y,special)
                            entity = empty[runIdB].newElement(S.RelEntity)
                            entity.type = eType
                            entity.token = token
                            entity.semanticId = '0'
                            entity.meta_annotation = 'binariser'
                            node = empty[runIdB].newElement(S.RelNode)
                            node.entity = entity
                            node_map[runIdB][runId] = node
                            result[runIdB].add_node(node)
                    elif pred=='edge':
                        tmp3 = PrologConverter.reEdgeArgs.search(args)
                        if tmp3:
                            runId1,runId2,edgeType = tmp3.groups()
                            edge = empty[runIdB].newElement(S.RelEdge)
                            edge.type = edgeType
                            edge.bgn = node_map[runIdB][runId1]
                            edge.end = node_map[runIdB][runId2]
                            result[runIdB].add_edge(node_map[runIdB][runId1],
                                                    node_map[runIdB][runId2],
                                                    edge)
        return(result)
