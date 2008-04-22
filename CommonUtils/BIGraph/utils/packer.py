import sys
import networkx as NX
import networkx.cliques as C
from BIGraph import *
from BIGraph.core.sentence import *

class Dummy:
    def __init__(self,node,entity):
        self.node = node
        self.entity = entity

class Packer:
    """
    No new nodes or edges are created.
    """
    def __init__(self):
        self.mapping = []

    def pack(self,G):
        """
        Packs a single graph. Operates on strings only. Nodes are
        dummy objects that wrap node id and entity id (in 'node' and
        'entity' variables) while edges are strings.

        @param G: input graph
        @type G: networkx.XDiGraph instance
        """
        finished = False
        while not finished:
            finished = True
            finished = finished and Packer._loop(self._packOutIdentical,G)
            finished = finished and Packer._loop(self._packInIdentical,G)
            finished = finished and Packer._loop(self._packAgpat,G)

    def _packOutIdentical(self,group,G):
        """
        Merges nodes of identical entities with identical out-edges.

        @param group: group of nodes of identical entities
        @type group: list
        @param G: input graph
        @type G: networkx.XDiGraph instance
        @return: True if no changes were made
        @rtype: boolean
        """
        for (p1,p2) in Packer._makePairs(group):
            if not Packer._diffOutEdges(p1,p2,G):
                for (a,b,c) in G.in_edges(p1):
                    self.mapping.append( ('edge-move',
                                          (a.node,b.node,c),
                                          (a.node,p2.node,c),
                                          '_packOutIdentical') )
                    G.delete_edge(a,b,c)
                    G.add_edge(a,p2,c)
                for (a,b,c) in G.out_edges(p1):
                    self.mapping.append( ('edge-delete',
                                          (a.node,b.node,c),
                                          '_packOutIdentical') )
                self.mapping.append( ('node-delete',p1.node,
                                      '_packOutIdentical') )
                G.delete_node(p1)
                return(False)
        return(True)

    def _packInIdentical(self,group,G):
        """
        Merges nodes of identical entities with identical in-edges.

        @param group: group of nodes of identical entities
        @type group: list
        @param G: input graph
        @type G: networkx.XDiGraph instance
        @return: True if no changes were made
        @rtype: boolean
        """
        for (p1,p2) in Packer._makePairs(group):
            if not Packer._diffInEdges(p1,p2,G):
                d = Packer._diffOutEdges(p1,p2,G)
                types = set( map(lambda x:x[1],d) )
                if len(types)==0:
                    # nodes are exactly identical
                    for (a,b,c) in G.in_edges(p2):
                        self.mapping.append( ('edge-delete',
                                              (a.node,b.node,c),
                                              '_packInIdentical') )
                    for (a,b,c) in G.out_edges(p2):
                        self.mapping.append( ('edge-delete',
                                              (a.node,b.node,c),
                                              '_packInIdentical') )
                    self.mapping.append( ('node-delete',p2.node,
                                          '_packInIdentical') )
                    G.delete_node(p2)
                    return(False)
                elif len(types)==1 and not 'agpat' in types:
                    # differences in one edge type
                    for (a,b,c) in G.out_edges(p2):
                        if (b,c) in d:
                            self.mapping.append( ('edge-move',
                                                  (a.node,b.node,c),
                                                  (p1.node,b.node,c),
                                                  '_packInIdentical') )
                            G.delete_edge(a,b,c)
                            G.add_edge(p1,b,c)
                        else:
                            self.mapping.append( ('edge-delete',
                                                  (a.node,b.node,c),
                                                  '_packInIdentical') )
                    for (a,b,c) in G.in_edges(p2):
                        self.mapping.append( ('edge-delete',
                                              (a.node,b.node,c),
                                              '_packInIdentical') )
                    self.mapping.append( ('node-delete',p2.node,
                                          '_packInIdentical') )
                    G.delete_node(p2)
                    return(False)
        return(True)

    def _packAgpat(self,group,G):
        """
        Merges nodes of identical entities with identical edges
        (except out-going agpats).

        @param group: group of nodes of identical entities
        @type group: list
        @param G: input graph
        @type G: networkx.XDiGraph instance
        @return: True if no changes were made
        @rtype: boolean
        """
        pairs = []
        # find all parent nodes that differ only by agpat
        for (p1,p2) in Packer._makePairs(group):
            if not Packer._diffInEdges(p1,p2,G):
                d = Packer._diffOutEdges(p1,p2,G)
                types = map(lambda x: x[1],d)
                if len(types)==0:
                    # nodes are exactly identical
                    for (a,b,c) in G.in_edges(p2):
                        self.mapping.append( ('edge-delete',
                                              (a.node,b.node,c),
                                              '_packAgpat') )
                    for (a,b,c) in G.out_edges(p2):
                        self.mapping.append( ('edge-delete',
                                              (a.node,b.node,c),
                                              '_packAgpat') )
                    self.mapping.append( ('node-delete',p2.node,
                                          '_packAgpat') )
                    G.delete_node(p2)
                    return(False)
                if all([x=='agpat' for x in types]):
                    # differences in agpats
                    pairs.append( (p1,p2) )

        unchanged = True
        if pairs:
            # find clusters of agpats
            # (transitivity)
            H = NX.Graph()
            for (a,b) in pairs:
                H.add_edge(a,b)
            # for each cluster, pack the cluster if possible
            for sub in NX.connected_components(H):
                unchanged = unchanged and self._processAgpat(sub,G)
        return(unchanged)

    def _processAgpat(self,sub,G):
        """
        Workhorse function for packing agpats.
        """
        # original 'agpat' edges
        oldEdges = [edge
                    for node in sub
                    for edge in G.out_edges(node) if edge[2]=='agpat']

        # find all possible agpat child pairs
        I = NX.Graph()
        # all nodes have to be present (some can be lone ones)
        for x in oldEdges:
            I.add_node(x[1])
        for (c,d) in Packer._makePairs([x[1] for x in oldEdges]):
            I.add_edge(c,d)

        # find all cliques
        # (sorted by size)
        cliques = C.find_cliques(I)
        newLen = reduce(lambda x,y:x+len(y), cliques, 0)
        
        # proceed if new grouping use less edges that the original
        # (rearrange edges)
        unchanged = True
        if newLen<len(oldEdges):
            # pick an edge for each child in each clique..
            edge_map = {}
            for clique in cliques:
                for node in clique:
                    if not edge_map.has_key(node):
                        edge_map[node] = []
                    current = [e for e in oldEdges if e[1]==node][0]
                    edge_map[node].append(current)
                    oldEdges.remove(current)
            # and remove unneeded edges
            for (a,b,c) in oldEdges:
                self.mapping.append( ('edge-delete',
                                      (a.node,b.node,c),
                                      '_packAgpat') )
                G.delete_edge(a,b,c)
            
            # pack each group..
            while cliques:
                children = cliques.pop(0)
                parent = sub.pop(0)
                # connect children to the parent
                for node in children:
                    (p1,p2,e) = edge_map[node].pop(0)
                    self.mapping.append( ('edge-move',
                                          (p1.node,p2.node,e),
                                          (parent.node,node.node,e),
                                          '_packAgpat') )
                    G.delete_edge(p1,p2,e)
                    G.add_edge(parent,node,e)
            # and remove unneeded parents
            for node in sub:
                self.mapping.append( ('node-delete',node.node,
                                      '_packAgpat') )
                G.delete_node(node)
            unchanged = False
        
        return(unchanged)

    @classmethod
    def _loop(cls,func,G):
        """
        Loops over a packing method until no changes are made.

        @param func: packing method
        @type func: function
        @param G: input graph
        @type G: networkx.XDiGraph instance
        @return: True if changes were made
        @rtype: boolean
        """
        def collect(G):
            """
            Collects nodes by entity id.
            """
            result = []
            for a in G.nodes():
                newnode = True
                for b in range(len(result)):
                    if a.entity==result[b][0].entity:
                        result[b].append(a)
                        newnode = False
                        break
                if newnode:
                    result.append([a])
            return(result)
        
        unchanged = True
        done = False
        while not done:
            groups = collect(G)
            done = True
            while groups:
                tmp = func(groups.pop(0),G)
                if not tmp:
                    groups = collect(G)
                unchanged = unchanged and tmp
                done = done and tmp
        return(unchanged)

    @classmethod
    def _makePairs(cls,group):
        """
        Forms pairs of nodes for comparison and (possibly) merging.

        @param group: group of nodes
        @type group: list
        @return: list of pairs
        @rtype: list
        """
        result = []
        l = len(group)
        for a in range(0,l):
            for b in range(a+1,l):
                result.append( (group[a],group[b]) )
        return(result)

    @classmethod
    def _diffOutEdges(cls,node1,node2,G):
        """
        Returns a symmetric difference in out-edges of two nodes.

        @param node1: node1
        @type node1: dummy object
        @param node2: node2
        @type node2: dummy object
        @return: symmetric difference of out-edges
        @rtype: set
        """
        # (y,z) given x is unique by specifications
        set1 = set([(y,z) for (x,y,z) in G.out_edges(node1)])
        set2 = set([(y,z) for (x,y,z) in G.out_edges(node2)])
        return(set2 ^ set1)

    @classmethod
    def _diffInEdges(cls,node1,node2,G):
        """
        Returns a symmetric difference in in-edges of two
        nodes. Agpats are always included in the result.

        @param node1: node1
        @type node1: dummy object
        @param node2: node2
        @type node2: dummy object
        @return: symmetric difference of in-edges
        @rtype: set
        """
        # (x,z) given x is unique by specifications
        set1 = set([(x,z) for (x,y,z) in G.in_edges(node1) if not z=='agpat'])
        set2 = set([(x,z) for (x,y,z) in G.in_edges(node2) if not z=='agpat'])
        diff = set2 ^ set1
        # agpats are always a difference
        diff |= set([(x,z) for (x,y,z) in G.in_edges(node1) if z=='agpat'])
        diff |= set([(x,z) for (x,y,z) in G.in_edges(node2) if z=='agpat'])
        return(diff)
