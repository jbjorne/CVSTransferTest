import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class EQUAL(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self,removePredicate=True):
        G = self.sentence.interactions
        for n in [x for x in G.nodes() if x.entity.type=='EQUAL']:
            self.isValid(n) # force execution but report errors
            self.resolveAlias(n)
            if removePredicate:
                self.removePred(n)

    def remove(self,removeAlias=False):
        G = self.sentence.interactions
        for n in [x for x in G.nodes() if x.entity.type=='EQUAL']:
            self.isValid(n) # force execution but report errors
            if removeAlias:
                self.removeAlias(n)
            else:
                self.removePred(n)

    def isValid(self,node):
        # plam type must be EQUAL
        if not self.hasValidType(node,"EQUAL"):
            return(False)
        # EQUAL must not be nested
        if not self.isTop(node):
            return(False)
        # EQUAL must have only/exactly 'agent' and 'patient' edges out
        if not self.hasExactlyAgentPatient(node):
            return(False)
        # aliases should not be involved in any other relationships
        # (refiner should be able to handle some of these cases)
        G = self.sentence.interactions
        tmp = collectByType(node,G)
        for alias in tmp['out']['patient']:
            if G.out_edges(alias):
                # EQUAL is used for physical entities only ->
                # out-going edges should always be ok
                self.pw("alias has outgoing edges",
                        formatRelNodeFull(alias))
            for x in G.in_edges(alias):
                # in-coming EQUALs are ok, others are not
                if not x[0].entity.type=='EQUAL':
                    self.pe("invalid alias (non-EQUAL incoming edge)",
                            formatRelNodeFull(alias))
                    return(False)
        return(True)

    def resolveAlias(self,node):
        G = self.sentence.interactions
        edges = G.out_edges(node)
        for agent in [x[1] for x in edges if x[2].type=='agent']:
            for patient in [x[1] for x in edges if x[2].type=='patient']:
                # copy in-edges only from non-EQUAL to avoid duplicates
                copyme = set([x for x in G.in_neighbors(agent)
                              if not x.entity.type=='EQUAL'])
                for e in copyme:
                    newParent = self.sentence.copyRelNode(e)
                    for f in [x for x in G.out_edges(newParent)
                              if x[1]==agent]:
                        G.delete_edge(f)
                        f[2].end = patient
                        G.add_edge(f[0],patient,f[2])
                # out-edges can are not copied
                # (assuming only physical entities are involved)
                self.pm( "edges copied",
                         "%s to %s"%(formatRelNodeFull(agent),
                                     formatRelNodeFull(patient)) )

    def removeAlias(self,n):
        G = self.sentence.interactions
        for alias in [y for (x,y,z) in G.out_edges(n)
                      if z.type=='patient']:
            G.delete_node(alias)
            self.pm("node removed",formatRelNodeFull(alias))
        self.removePred(n)
