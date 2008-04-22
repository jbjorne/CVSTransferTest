import sys
from BIGraph.core.sentence import *
from BIGraph.refiners import *
from BIGraph.utils.packer import Packer,Dummy

class Pack(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        """
        Packs an interaction graph in a single sentence.
        """
        G = self.sentence.interactions
        
        # create suitable graph
        nodes = {}
        edges = {}
        tmpMap = {}
        tmpG = NX.create_empty_copy(G) # empty graph of identical type
        for x in G.nodes():
            tmp = Dummy(x.id,x.entity)
            tmpG.add_node(tmp)
            tmpMap[x] = tmp
            nodes[x.id] = x
        for (x,y,z) in G.edges():
            tmpG.add_edge( (tmpMap[x],tmpMap[y],z.type) ) # unique by specs
            edges[ (x.id,y.id,z.type) ] = (x,y,z)

        # calculate changes
        packer = Packer()
        packer.pack(tmpG)

#         # for debugging
#         for a in packer.mapping:
#             print a
        
        # apply changes
        for a in packer.mapping:
            cmd = a[0]
            if cmd=='node-delete':
                G.delete_node(nodes[a[1]])
                del nodes[a[1]]
                self.pm("node deleted", "%s"%str(a[1]))
            elif cmd=='edge-delete':
                G.delete_edge(edges[a[1]])
                del edges[a[1]]
                self.pm("edge deleted", "%s"%str(a[1]))
            elif cmd=='edge-move':
                oldEdge = edges[a[1]]
                G.delete_edge(oldEdge)
                del edges[a[1]]
                nbgn,nend,ntype = a[2]
                oldEdge[2].type = ntype
                oldEdge[2].bgn = nodes[nbgn]
                oldEdge[2].end = nodes[nend]
                newEdge = (nodes[nbgn],nodes[nend],oldEdge[2])
                G.add_edge(newEdge)
                edges[a[2]] = newEdge
                self.pm("edge moved", "%s >> %s"%(str(a[1]),str(a[2])))

    def remove(self):
        self.pe("remove-method not supported","")
