"""
Coreference resolution.
"""
import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class COREFER(Refiner):
    """
    A class for coreference resolution.

    In the resolution procedure, COREFER
    nodes are analysed for referent nodes and reference nodes.
    The found referent nodes are copied and placed
    to the equal context with the reference nodes. Optionally, the
    reference nodes can be removed at the end of the procedure.
    
    Alternatively, COREFER nodes can be removed without resolving 
    the coreference.
    """
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self,removePredicate=True,removeReference=True):
        G = self.sentence.interactions
        unprocessed = set(x for x in G.nodes() if x.entity.type=='COREFER')
        while unprocessed:
            ref = unprocessed.pop()
            self.isValid(ref) # force execution but report errors
            self.resolveReference(ref,unprocessed,removeReference)
            if removePredicate or removeReference:
                self.removePred(ref)

    def remove(self):
        G = self.sentence.interactions
        for ref in [x for x in G.nodes() if x.entity.type=='COREFER']:
            self.isValid(ref) # force execution but report errors
            self.removePred(ref)

    def isValid(self,node):
        # plam type must be COREFER
        if not self.hasValidType(node,"COREFER"):
            return(False)
        # COREFER must not be nested
        if not self.isTop(node):
            return(False)
        # COREFER must have only/exactly 'agent' and 'patient' edges out
        if not self.hasExactlyAgentPatient(node):
            return(False)
        G = self.sentence.interactions
        tmp = collectByType(node,G)
        # agents (references) must be leafs (in BioInfer by definition)
        for agent in tmp['out']['agent']:
            if G.out_edges(agent):
                self.pe("invalid reference (outgoing edges)",
                        formatRelNodeFull(agent))
                return(False)
        return(True)
    
    def resolveReference(self,node,unprocessed,removeReference):
        G = self.sentence.interactions
        edges = G.out_edges(node)
        patients = [x[1] for x in edges if x[2].type=='patient']
        # each agent can be dealt individually
        for agent in [x[1] for x in edges if x[2].type=='agent']:
            # any unprocessed COREFERs to this agent
            corefer = unprocessed & set(x for x in G.in_neighbors(agent)
                                        if x.entity.type=='COREFER')
            for patient in patients:
                # the original relationship must be saved if:
                # - reference must be preserved or
                # - there are other COREFERs to be processed or
                # - there are other patients to be processed
                makecopy = (not removeReference) or \
                           corefer or \
                           (patients.index(patient)-len(patients) < -1)
                if makecopy:
                    newCopy = self.sentence.copyRelNode(agent)
                else:
                    newCopy = agent
                for f in G.in_edges(newCopy):
                    # copy only those in-edges that come from non-COREFER
                    # (COREFERs are not copied because they would be invalid
                    # in the duplicates)
                    # (no out-edges in agent)
                    G.delete_edge(f)
                    if not f[0].entity.type=='COREFER':
                        f[2].end = patient
                        G.add_edge(f[0],patient,f[2])
                # delete the reference copy
                if makecopy:
                    G.delete_node(newCopy)
                # patient has its own relationships which must/will
                # remain unchanged
                self.pm( "edges copied",
                         "%s to %s"%(formatRelNodeFull(agent),
                                     formatRelNodeFull(patient)) )
            if removeReference and not corefer:
                # this reference is fully processed and can be deleted
                # (since it's a leaf, it can simply be deleted)
                G.delete_node(agent)
                self.pm("node removed",formatRelNodeFull(agent))
