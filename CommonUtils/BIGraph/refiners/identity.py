import networkx as NX
from BIGraph.core.sentence import *
from BIGraph.refiners import *

class Identity(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)
    
    def resolve(self):
        G = self.sentence.interactions
        # Process all edges in the interaction graph whose type is "identity"
        for edge in [x for x in G.edges() if x[2].type=='identity']:
            # edgesTo contains all edges coming to a node that also has an 
            # edge of type "identity" leaving from it
            edgesTo = G.in_edges_iter([edge[0]])
            
            # Loop through all edges coming to the node and check that
            # none of them have the type "identity". This means that
            # the node is the first node in a chain of "identity"-edges 
            isFirstIdentityEdge = True
            for edgeTo in edgesTo:
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
                while edgesFrom != None and len(edgesFrom) > 0:
                    nextEdge = None
                    for edgeFrom in edgesFrom:
                        # This is the next link in the identity chain
                        if edgeFrom.type == "identity":
                            assert(nextEdge == None)
                            nextEdge = edgeFrom
                    if nextEdge != None:
                        currentEdge = nextEdge
                        edgesFrom = G.out_edges_iter([nextEdge[1]])
                    else:
                        edgesFrom = None
            
            # Relink all edges coming to the first node of the "identity"-chain
            # to the last node of the chain.
            for edge in edgesTo:
                G.delete_edge(edge)
                G.addEdge(edge[0], )