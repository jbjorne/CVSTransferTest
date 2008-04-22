import networkx as NX
from BIGraph.core.sentence import *
from BIGraph.refiners import *

# data on nesting relationships

# NOTE: this data should be embedded in the relentity vocabulary
#       (which would make it more like an ontology)

lists = []
# protein/RNA/DNA from 'smallest' to 'largest':
lists.append(['Amino_acid_monomer',
              'Peptide',
              'Substructure_of_protein',
              'Individual_protein',
              'Protein_complex',
              'Protein_family_or_group'])
lists.append(['Individual_protein',
              'Fusion_protein'])
lists.append(['Nucleotide',
              'Polynucleotide'])
lists.append(['Polynucleotide',
              'Domain_or_region_of_RNA',
              'Individual_RNA_molecule',
              'RNA_family_or_group'])
lists.append(['Polynucleotide',
              'Domain_or_region_of_DNA',
              'Gene',
              'Individual_DNA_molecule',
              'DNA_family_or_group'])
# NOTES:
# 'Gene' may cause errors
# 'Substructure' may be larger than 'Domain_or_region'

# other physical entities:
lists.append(['Atom',
              'Compound']),
lists.append(['Cell_component',
              'Cell_type',
              'Tissue',
              'Body_part',
              'Organism'])
# NOTES:
# missing (unneeded?) types: mono/multi-cell-organism, virus, cell-line

# linker edges
lists.append(['Compound',
              'Amino_acid_monomer'])
lists.append(['Compound',
              'Nucleotide'])
lists.append(['Protein_family_or_group',
              'Cell_component'])
lists.append(['RNA_family_or_group',
              'Cell_component'])
lists.append(['DNA_family_or_group',
              'Cell_component'])

# generate graphs
# size relations (larger -> smaller)
graph_nesting_physical = NX.DiGraph()
for a in lists:
    for b in range(len(a)-1):
        graph_nesting_physical.add_edge(a[b+1],a[b])
# protein/RNA/DNA encoding relations (encoding -> encoded)
graph_nesting_encoding = NX.DiGraph()
graph_nesting_encoding.add_edge('DNA','RNA')
graph_nesting_encoding.add_edge('RNA','Protein')
graph_nesting_encoding.add_edge('RNA','Peptide')

def getNesting(ulp):
    tokens = (ulp[0].entity.token.getNested(),
              ulp[1].entity.token.getNested())
    whole = tokens[0][:]
    unnested = tokens[0][:]
    nested = tokens[1][:]
    for a in nested:
        if a in unnested:
            unnested.remove(a)
    return( (whole,unnested,nested) )

class PrepAnalyser:
    # default and alternate groups must include all preps present in any of
    # the lists
    edges = {'default': {'by': 'agent',
                         'of': 'patient',
                         # patient get priority if no preps present
                         '': 'patient'},
             'alternate': {'from': 'agent',
                           'with': 'agent',
                           'on': 'patient',
                           'in': 'patient',
                           'to': 'patient',
                           'at': 'patient'},
             'effect': {'of': 'agent',
                        'on': 'patient',
                        '': 'agent'}
             }

    words = {'effect': 'effect',
             'effects': 'effect'}

    @classmethod
    def getKnownPreps(cls):
        return( set(y
                    for x in PrepAnalyser.edges.values()
                    for y in x.keys() if y) )
    
    @classmethod
    def resolve(cls,edge,instance):
        def useDefault(prep):
            # examine preposition
            if prep in PrepAnalyser.edges['default'].keys():
                return(PrepAnalyser.edges['default'][prep])
            else:
                # (unreliable -> issue a warning)
                instance.pw("unreliable resolution (weak preposition)",
                            formatRelEdge(edge))
                return(PrepAnalyser.edges['alternate'][prep])
            
        ontology = instance.ontologies['relentityvocabulary']
        # subtokens
        whole,unnested,nested = getNesting(edge)
        words = map(lambda a: a.text, unnested)
        # prepositions indicate a role
        knownPreps = PrepAnalyser.getKnownPreps()
        preps = set(x for x in words if x in knownPreps)
        nonpreps = set(words)-preps
        
        if len(nonpreps)==0:
            # only prepositions (should never occur)
            if len(preps)==0:
                instance.pe("no text",formatRelEdge(edge))
                return('')
            elif len(preps)==1:
                result = useDefault(preps.pop())
            else:
                instance.pe("two prepositions",formatRelEdge(edge))
                return('')

        elif len(nonpreps)==1:
            # one non-preposition
            word = nonpreps.pop()
            # examine preposition
            if len(preps)==0:
                prep = ''
            elif len(preps)==1:
                prep = preps.pop()
            else:
                instance.pe("two prepositions",formatRelEdge(edge))
                return('')
            if word in PrepAnalyser.words.keys():
                # use specific group if defined
                group = PrepAnalyser.words[word]
                if prep in PrepAnalyser.edges[group].keys():
                    result = PrepAnalyser.edges[group][prep]
                else:
                    # (unspecified -> issue a warning)
                    instance.pw("'%s' not specified for '%s' (using default)"%
                                (prep,word),
                                formatRelEdge(edge))
                    result = useDefault(prep)
            else:
                result = useDefault(prep)

        else:
            # more than one non-preposition
            # (cannot define specific group, if any)
            # (unreliable -> issue a warning)
            instance.pw("unreliable resolution (more than one non-prepositions)",
                        formatRelEdge(edge))
            if len(preps)==0:
                result = 'agent' # is good solution only for BioInfer?
            elif len(preps)==1:
                result = useDefault(preps.pop())
            else:
                instance.pe("two prepositions",formatRelEdge(edge))
                return('')
            
        # for symmetric processes, use 'agpat' instead of 'agent' or 'patient'
        if ontology.isSymmetric(edge[0].entity.type):
            result = 'agpat'

        return(result)
                
class Nesting(Refiner):
    def __init__(self,sentence,ontologies):
        Refiner.__init__(self,sentence,ontologies)

    def resolve(self):
        G = self.sentence.interactions
        for edge in [x for x in G.edges() if x[2].type=='nesting']:
            self.isValid(edge) # force execution but report errors
            self.resolveAny(edge)

    def remove(self):
       self.pe("remove-method not supported","")

    def isValid(self,edge):
        if not edge[2].type=='nesting':
            self.pe("invalid edge type",formatRelEdge(edge))
            return(False)
        return(True)

    def resolveAny(self,edge):
        types = (edge[0].entity.type,
                 edge[1].entity.type)
        ontology = self.ontologies['relentityvocabulary']
        
        # physical must nest physical
        if ontology.isPhysical(types[0]):
            if ontology.isPhysical(types[1]):
                return( self.resolvePhysical(edge) )
            else:
                self.pe("non-physical nested in physical",
                        formatRelEdge(edge))
        # process can nest anything
        if ontology.isProcess(types[0]):
            return( self.resolveProcess(edge) )
        # property can nest anything
        if ontology.isProperty(types[0]):
            return( self.resolveProperty(edge) )
        # this should never occur
        self.pe("unknown nesting",formatRelEdge(edge))
        return(False)

    def resolveProperty(self,edge):
        edge[2].type = 'possessor'
        self.pm("edge type resolved",formatRelEdge(edge))
        return(True)

    def resolveProcess(self,edge):
        result = PrepAnalyser.resolve(edge,self)
        if result:
            edge[2].type = result
            self.pm("edge type resolved",formatRelEdge(edge))
            return(True)
        self.pe("unknown nesting",formatRelEdge(edge))
        return(False)

    def resolvePhysical(self,edge):
        ontology = self.ontologies['relentityvocabulary']
        types = (edge[0].entity.type,
                 edge[1].entity.type)

        result = ''
        # if the types are identical and in the list,
        # use 'identity'
        # (list contains those that cannot have sub-/super-sets)
        if types[0]==types[1]:
            if types[0] in ['Individual_protein',
                            'Individual_RNA_molecule',
                            'Individual_DNA_molecule',
                            'Gene']:
                result = 'identity'
            # this is unreliable so issue a warning
            elif types[0] in ['Protein_family_or_group',
                              'Protein_complex',
                              'RNA_family_or_group',
                              'DNA_family_or_group']:
                result = 'identity'
                self.pw("unreliable resolution (identity vs. sub/super set)",
                        formatRelEdge(edge))
            # this is unreliable so issue a warning
            else:
                type_map = {-1:'sub',1:'super'}
                middles = ['Individual_protein',
                           'Individual_RNA_molecule',
                           'Individual_DNA_molecule',
                           'Gene']

                # prepositions divided by 'direction'
                forwardPreps = ['of','on','in','around','under']
                reversePreps = ['by','from']
                # subtokens
                whole,unnested,nested = getNesting(edge)
                words = map(lambda a: a.text, unnested)
                result = ''
                prep = 0
                # forwardPrep -> nested is to nesting what
                #                nesting is to middle-most in the chain
                if len(words)==1 or any(x in forwardPreps for x in words):
                    prep = 1
                elif any(x in reversePreps for x in words):
                    prep = -1

                size = 0
                # nesting is 'larger' than middle-most
                if any(NX.shortest_path(graph_nesting_physical,
                                        types[0],x) for x in middles):
                    # type is "larger" than middle one
                    # -> nesting is larger than nested
                    # -> nested is smaller than nesting
                    size = 1
                # nesting is 'smaller' than middle-most
                elif any(NX.shortest_path(graph_nesting_physical,
                                          x,types[0]) for x in middles):
                    # type is "smaller" than middle one
                    # -> nesting is smaller than nested
                    # -> nested is larger than nesting
                    size = -1
                
                if not prep*size==0:
                    result = type_map[prep*size]
                    self.pw("highly unreliable resolution (using prepositions)",
                            formatRelEdge(edge))
                        
        # successor is 'smaller' than predecessor
        elif NX.shortest_path(graph_nesting_physical,
                              types[0],types[1]):
            result = 'sub'
            
        # successor is 'larger' than predecessor
        elif NX.shortest_path(graph_nesting_physical,
                              types[1],types[0]):
            result = 'super'
            
        # successor is encoded by predecessor
        elif NX.shortest_path(graph_nesting_encoding,
                              ontology.getPhysicalType(types[0]),
                              ontology.getPhysicalType(types[1])):
            result = 'identity'
            
        # successor encodes predecessor
        elif NX.shortest_path(graph_nesting_encoding,
                              ontology.getPhysicalType(types[1]),
                              ontology.getPhysicalType(types[0])):
            result = 'identity'
            
        # special types
        # NOTE: for binarisation,
        #       these can be safely approximated to 'identity'
        elif types[0]=="Mutant":
            # result = 'mutant'
            result = 'identity'
        elif types[0]=="Analog":
            # result = 'analog'
            result = 'identity'
        elif types[0]=="Homolog":
            # result = 'homolog'
            result = 'identity'

        if result:
            edge[2].type = result
            self.pm("edge type resolved",formatRelEdge(edge))
            return(True)
        self.pe("unknown nesting",formatRelEdge(edge))
        return(False)
