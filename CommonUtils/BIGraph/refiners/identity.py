import networkx as NX
from BIGraph.core.sentence import *
from BIGraph.refiners import *

# This refiner relinks edges that go to nodes that have leaving "identity"
# edges to the node at the end of the "identity"-edge chain.

class Identity(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)
    
    def resolve(self):
        G = self.sentence.interactions
        # Process all edges in the interaction graph whose type is "identity"
        for edge in [x for x in G.edges() if x[2].type=='identity']:
            #print "Found identity edge"
            # edgesTo contains all edges coming to a node that also has an 
            # edge of type "identity" leaving from it
            edgesTo = G.in_edges_iter([edge[0]])
            
            # Loop through all edges coming to the node and check that
            # none of them have the type "identity". This means that
            # the node is the first node in a chain of "identity"-edges 
            isFirstIdentityEdge = True
            for edgeTo in edgesTo:
                #print "EdgeTo:", edgeTo[2].type
                if edgeTo[2].type == "identity":
                    isFirstIdentityEdge = False
                    break
            
            # Go through the chain of "identity" edges to find the
            # last node in the chain.
            if isFirstIdentityEdge:
                # Loop through all the nodes leaving from the node.
                # At the end, currentEdge should contain the last
                # "identity"-edge in the chain.
                edgesFrom = G.out_edges_iter([edge[1]])
                currentEdge = edge
                while edgesFrom != None:
                    nextEdge = None
                    for edgeFrom in edgesFrom:
                        # This is the next link in the identity chain
                        if edgeFrom[2].type == "identity":
                            assert(nextEdge == None)
                            nextEdge = edgeFrom
                    if nextEdge != None:
                        currentEdge = nextEdge
                        edgesFrom = G.out_edges_iter([nextEdge[1]])
                    else:
                        edgesFrom = None
            
                # Relink all edges coming to the first node of the "identity"-chain
                # to the last node of the chain.
                edgesTo = G.in_edges_iter([edge[0]])
                edgesToDelete = []
                for edgeTo in edgesTo:
                    edgesToDelete.append(edgeTo)
                    edgeTo[2].end = currentEdge[1]
                    G.add_edge(edgeTo[0],currentEdge[1],edgeTo[2])
                    #G.add_edge(currentEdge[1],edgeTo[0],edgeTo[2])
                for edgeToDelete in edgesToDelete:
                    G.delete_edge(edgeToDelete)