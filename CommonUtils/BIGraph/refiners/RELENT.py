import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class RELENT(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self,removePredicate=True):
        G = self.sentence.interactions
        for rel in [x for x in G.nodes()
                    if x.entity.type=='REL-ENT']:
            self.isValid(rel) # force execution but report errors
            self.resolveReference(rel)
            if removePredicate:
                self.removePred(rel)

    def remove(self):
        G = self.sentence.interactions
        for rel in [x for x in G.nodes()
                    if x.entity.type=='REL-ENT']:
            self.isValid(rel) # force execution but report errors
            self.removePred(rel)

    def isValid(self,node):
        # plam type must be REL-ENT
        if not self.hasValidType(node,"REL-ENT"):
            return(False)
        # REL-ENT must not be nested
        if not self.isTop(node):
            return(False)
        # REL-ENT must have only/exactly 'agent' and 'patient' edges out
        if not self.hasExactlyAgentPatient(node):
            return(False)
        G = self.sentence.interactions
        tmp = collectByType(node,G)
        # Agents (references) must be leafs (in BioInfer by definition).
        # However, partially processed agents will fail this test ->
        # just issue a warning. Agents should be physical entities ->
        # existing out-going edges should be interfere with new ones.
        for agent in tmp['out']['agent']:
            if G.out_edges(agent):
                self.pw("reference has outgoing edges",
                        formatRelNodeFull(agent))
                return(False)
        return(True)
    
    def resolveReference(self,rel):
        G = self.sentence.interactions
        edges = G.out_edges(rel)
        for agent in [x[1] for x in edges if x[2].type=='agent']:
            for patient in [x[1] for x in edges if x[2].type=='patient']:
                newEdge = self.sentence.newElement(RelEdge)
                newEdge.type='nesting'
                newEdge.bgn = agent
                newEdge.end = patient
                G.add_edge(agent,patient,newEdge)
                self.pm("edge added",formatRelEdge((agent,patient,newEdge)))
