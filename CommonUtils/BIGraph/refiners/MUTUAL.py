import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class MUTUAL(Refiner):
    mapping = {'MUTUAL-AFFECT': 'AFFECT',
               'MUTUALCONDITION': 'CONDITION'}
    
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        G = self.sentence.interactions
        for rel in [x for x in G.nodes()
                    if x.entity.type in MUTUAL.mapping.keys()]:
            self.isValid(rel) # force execution but report errors
            self.resolveMutual(rel)

    def remove(self):
        self.pe("remove-method not supported",self.sentence.id)

    def isValid(self,node):
        # node type must be in the mapping
        if not node.entity.type in MUTUAL.mapping.keys():
            self.pe("invalid type",formatRelNodeFull(node))
            return(False)
        G = self.sentence.interactions
        edges = G.out_edges(node)
        # must have exactly two agpat edges out
        if not len(edges)==2:
            self.pe("not exactly two outgoing edges",
                    formatRelNodeFull(node))
            return(False)
        if any([x[2].type!='agpat' for x in edges]):
            self.pe("non-agpat outgoing edges",
                    formatRelNodeFull(node))
            return(False)
        return(True)

    def resolveMutual(self,rel):
        G = self.sentence.interactions

        oldType = rel.entity.type
        rel.entity.type = MUTUAL.mapping[rel.entity.type]
        edges = G.out_edges(rel)
        edges[0][2].type = 'agent'
        edges[1][2].type = 'patient'

        relCopy = self.sentence.copyRelNode(rel)
        edges = G.out_edges(relCopy)
        # makes sure that edge types are switched
        for a in edges:
            if a[2].type == 'agent':
                a[2].type = 'patient'
            elif a[2].type == 'patient':
                a[2].type = 'agent'
        
        self.pm("%s processed into %s"%(oldType,rel.entity.type),
                formatRelNodeFull(rel))
