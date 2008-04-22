import sys
import re
import copy
import inspect
import pylab as P
import Tkinter as TK
import networkx as NX
from BIGraph import *
from BIGraph.core.corpus import Corpus
from BIGraph.core.sentence import Sentence
from BIGraph.refiners import CorpusRefiner
from BIGraph.refiners.NOT import NOT
from BIGraph.refiners.EQUAL import EQUAL
from BIGraph.refiners.COREFER import COREFER
from BIGraph.refiners.RELENT import RELENT
from BIGraph.refiners.MUTUAL import MUTUAL
from BIGraph.refiners.nesting import Nesting
from BIGraph.binariser.binariser import Binariser
from BIGraph.binariser.verify import Verify
from BIGraph.refiners.pack import Pack

class Plotter:
    def __init__(self,corpus,rules=None,verify="approved-binary-interactions"):
        self.corpus = corpus
        self.rules = rules
        self.verify = Verify(verify)
        self.filt = lambda a:True
        self.current = 0
        self.pairs = []
        self.curPairs = None
        self.binarised_sentence = None
        
        root = TK.Tk()
        self.query = TK.StringVar(root)

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Navigation:").pack(side='left')
        TK.Button(tmp,text="Draw",command=self.drawCurrent).pack(side='left')
        TK.Button(tmp,text="Prev",command=self.drawPrev).pack(side='left')
        TK.Button(tmp,text="Next",command=self.drawNext).pack(side='left')
        TK.Button(tmp,text="Prev pair",command=self.prevPairs).pack(side='left')
        TK.Button(tmp,text="Next pair",command=self.nextPairs).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Query:").pack(side='left')
        TK.Entry(tmp,textvariable=self.query).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Query filters:").pack(side='left')
        TK.Button(tmp,text="Reset filter",command=self.resetFilter).pack(side='left')
        TK.Button(tmp,text="By number",command=self.findSentenceById).pack(side='left')
        TK.Button(tmp,text="By type",command=self.findSentenceByType).pack(side='left')
        TK.Button(tmp,text="By text",command=self.findSentenceByText).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Special filters:").pack(side='left')
        TK.Button(tmp,text="NOT",command=self.findNot).pack(side='left')
        TK.Button(tmp,text="EQUAL",command=self.findEqual).pack(side='left')
        TK.Button(tmp,text="COREFER",command=self.findCorefer).pack(side='left')
        TK.Button(tmp,text="REL-ENT",command=self.findRelent).pack(side='left')
        TK.Button(tmp,text="MUTUAL",command=self.findMutual).pack(side='left')
        TK.Button(tmp,text="Nesting",command=self.findNesting).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Resolve:").pack(side='left')
        TK.Button(tmp,text="All",command=self.resolveAll).pack(side='left')
        TK.Button(tmp,text="NOT",command=self.processNot).pack(side='left')
        TK.Button(tmp,text="EQUAL",command=self.processEqual).pack(side='left')
        TK.Button(tmp,text="COREFER",command=self.processCorefer).pack(side='left')
        TK.Button(tmp,text="REL-ENT",command=self.processRelent).pack(side='left')
        TK.Button(tmp,text="MUTUAL",command=self.processMutual).pack(side='left')
        TK.Button(tmp,text="Nesting",command=self.processNesting).pack(side='left')
        TK.Button(tmp,text="Pack",command=self.packGraph).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Remove:").pack(side='left')
        TK.Button(tmp,text="NOT",command=self.processNotRemove).pack(side='left')
        TK.Button(tmp,text="EQUAL",command=self.processEqualRemove).pack(side='left')
        TK.Button(tmp,text="COREFER",command=self.processCoreferRemove).pack(side='left')
        TK.Button(tmp,text="REL-ENT",command=self.processRelentRemove).pack(side='left')
        TK.Button(tmp,text="MUTUAL",command=self.processMutualRemove).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Candidate graphs:").pack(side='left')
        TK.Button(tmp,text="Generate graphs",command=self.generatePairs).pack(side='left')
        TK.Button(tmp,text="Remove graphs",command=self.removePairs).pack(side='left')

        tmp = TK.Frame(root)
        tmp.pack()
        TK.Label(tmp,text="Binarisation:").pack(side='left')
        TK.Button(tmp,text="Resolve one",command=self.binariseOne).pack(side='left')
        TK.Button(tmp,text="Resolve all",command=self.binariseAll).pack(side='left')
        TK.Button(tmp,text="Compare",command=self.compare).pack(side='left')
        TK.Button(tmp,text="Approve",command=self.approve).pack(side='left')

        P.show()
        root.mainloop()



# ----
# plotting functions (require pylab package)
# ----

    @classmethod
    def findLabels(cls,G):
        result = {}
        for p in G.nodes():
            result[p] = "%s | %s\n%s\n%s"%(p.id,p.entity.id,
                                           p.entity.type,
                                           p.entity.token.getText())
        return(result)

    @classmethod
    def hierarchical_layout(cls,G): # layout generator for networkx
        def repeat(v,x):
            result = []
            for a in range(x):
                result.append(v)
            return(result)
    
        result = {}
        layers = []
        tmp = G.nodes()
        used = dict( zip(tmp,repeat(False,len(tmp))) )
        # from up to down in layers
        nodes = set( [x for x in G.nodes() if len(G.in_neighbors(x))==0] )
        while nodes:
            remove = set([])
            for a in nodes:
                notused = [x for (x,y) in used.items() if not y]
                for b in G.in_neighbors(a):
                    if b in nodes or b in notused:
                        remove.add(a)
            remain = nodes - remove
            for a in remain:
                used[a] = True
            layers.insert(0,list(remain))
            nodes = set([])
            for a in remain:
                for b in G.out_neighbors(a):
                    nodes.add(b)
        # calculate coordinates
        xoff = 0.0
        yoff = 0.0
        xrng = 10.0
        yrng = 10.0
        ycnt = len(layers)+1
        ydlt = yrng/ycnt
        for a in range(len(layers)):
            xcnt = len(layers[a])+1
            xdlt = xrng/xcnt
            yincr = ydlt/len(layers[a])
            y = yoff + (a+1)*ydlt
            for b in range(len(layers[a])):
                x = xoff + (b+1)*xdlt
                result[layers[a][b]] = (x,y+b*yincr)
        return(result)



# ----
# filtering functions
# ----

    def resetFilter(self):
        self.filt = lambda a:True
    def findNot(self):
        self.filt = lambda a: len([x for x in a.nodes()
                                   if x.entity.type=="NOT"])
    def findEqual(self):
        self.filt = lambda a: len([x for x in a.nodes()
                                   if x.entity.type=="EQUAL"])
    def findCorefer(self):
        self.filt = lambda a: len([x for x in a.nodes()
                                   if x.entity.type=="COREFER"])
    def findRelent(self):
        self.filt = lambda a: len([x for x in a.nodes()
                                   if x.entity.type=="REL-ENT"])
    def findMutual(self):
        self.filt = lambda a: len([x for x in a.nodes()
                                   if x.entity.type.startswith("MUTUAL")])
    def findNesting(self):
        self.filt = lambda a: len([x for x in a.edges()
                                   if x[2].type=="nesting"])
    def findSentenceById(self):
        self.filt = lambda a: a.nodes()[0].id.split('.')[1]==self.query.get()
    def findSentenceByType(self):
        tmp = re.compile(self.query.get())
        self.filt = lambda a: any([x for x in a.nodes()
                                   if tmp.search(x.entity.type)])
    def findSentenceByText(self):
        tmp = re.compile(self.query.get())
        self.filt = lambda a: any([x for x in a.nodes()
                                   if tmp.search(x.entity.token.getText())])



# ----
# processing functions
# ----

    def resolveAll(self):
        self.processNot()
        self.processEqual()
        self.processCorefer()
        self.processRelent()
        self.processMutual()
        self.processNesting()
        self.packGraph()

    def packGraph(self):
        CorpusRefiner(self.corpus,Pack).resolveAll()
        self.drawCurrent()
    def processNot(self):
        CorpusRefiner(self.corpus,NOT).resolveAll()
        self.drawCurrent()
    def processEqual(self):
        CorpusRefiner(self.corpus,EQUAL).resolveAll()
        self.drawCurrent()
    def processCorefer(self):
        CorpusRefiner(self.corpus,COREFER).resolveAll()
        self.drawCurrent()
    def processRelent(self):
        CorpusRefiner(self.corpus,RELENT).resolveAll()
        self.drawCurrent()
    def processMutual(self):
        CorpusRefiner(self.corpus,MUTUAL).resolveAll()
        self.drawCurrent()
    def processNesting(self):
        CorpusRefiner(self.corpus,Nesting).resolveAll()
        self.drawCurrent()

    def processNotRemove(self):
        CorpusRefiner(self.corpus,NOT).removeAll()
        self.drawCurrent()
    def processEqualRemove(self):
        CorpusRefiner(self.corpus,EQUAL).removeAll()
        self.drawCurrent()
    def processCoreferRemove(self):
        CorpusRefiner(self.corpus,COREFER).removeAll()
        self.drawCurrent()
    def processRelentRemove(self):
        CorpusRefiner(self.corpus,RELENT).removeAll()
        self.drawCurrent()
    def processMutualRemove(self):
        CorpusRefiner(self.corpus,MUTUAL).removeAll()
        self.drawCurrent()
    def processNestingRemove(self):
        CorpusRefiner(self.corpus,Nesting).removeAll()
        self.drawCurrent()

    def binariseOne(self):
        if self.pairs:
            sentence = copy.deepcopy(self.corpus.sentences[self.current])
            sentence.interactions = self.pairs[self.curPairs]
            Binariser.resolveSentence(sentence,
                                        self.corpus.vocabularies,
                                        self.rules,pack=False)
            self.binarised_sentence = sentence
            self.drawBin()

    def binariseAll(self):
        sentence = copy.deepcopy(self.corpus.sentences[self.current])
        Binariser.resolveSentence(sentence,
                                    self.corpus.vocabularies,
                                    self.rules)
        self.binarised_sentence = sentence
        self.drawBin()

# FIXME
    def compare(self):
        ids = sorted(self.verify.getIds())
        Gs = []
        current = 0
        while ids and current<len(self.corpus.sentences):
            sentence = self.corpus.sentences[current]
            uid = int(sentence.id)
            if uid in ids:
                ids.remove(uid)
                binSentence = copy.deepcopy(sentence)
                NOT.NOT(binSentence,self.corpus.vocabularies).resolve()
                EQUAL.EQUAL(binSentence,self.corpus.vocabularies).resolve()
                COREFER.COREFER(binSentence,self.corpus.vocabularies).resolve()
                RELENT.RELENT(binSentence,self.corpus.vocabularies).resolve()
                nesting.Nesting(binSentence,self.corpus.vocabularies).resolve()
                printError(self.__class__,
                           inspect.stack()[0][3],
                           "pack-method disabled")
                Binariser.resolveSentence(binSentence,
                                            self.corpus.vocabularies,
                                            self.rules)
                Gs.append(binSentence.interactions)
            current += 1

        (a,b) = self.verify.compare(Gs)
        print "---- Approved remains ----"
        print "\n".join(sorted(a))
        print "---- New remains ----"
        print "\n".join(sorted(b))

    def approve(self):
        self.verify.write(self.binarised_sentence.interactions)
# END FIXME
        



# ----
# drawing functions
# ----

    def drawNext(self):
        cur = self.current
        cur = (cur+1)%len(self.corpus.sentences)
        while not cur==self.current and \
                  not self.filt(self.corpus.sentences[cur].interactions):
            cur = (cur+1)%len(self.corpus.sentences)
        if not cur==self.current:
            self.current = cur
            self.drawCurrent()

    def drawPrev(self):
        cur = self.current
        cur = (cur-1)%len(self.corpus.sentences)
        while not cur==self.current and \
                  not self.filt(self.corpus.sentences[cur].interactions):
            cur = (cur-1)%len(self.corpus.sentences)
        if not cur==self.current:
            self.current = cur
            self.drawCurrent()

    def drawCurrent(self,labels=True):
        self.pairs = []
        self.curPairs = None
        self.binarised_sentence = None
        self.drawOrig()
        self.drawPair()
        self.drawBin()
    
    def drawOrig(self):
        sentence = self.corpus.sentences[self.current]
        G = sentence.interactions
        P.figure(1)
        P.clf()
        P.title("Original - #%s"%sentence.id)
        self.drawG(G)
    
    def drawPair(self):
        if self.pairs:
            G = self.pairs[self.curPairs]
            P.figure(2)
            P.clf()
            P.title("Pair - #%s"%self.curPairs)
            self.drawG(G)

    def drawBin(self):
        if self.binarised_sentence:
            G = self.binarised_sentence.interactions
        else:
            G = NX.XDiGraph()
        P.figure(3)
        P.clf()
        P.title("Binarised")
        self.drawG(G)

    def generatePairs(self):
        G = self.corpus.sentences[self.current].interactions
        self.pairs = Binariser.getPairs(G)
        self.curPairs = 0
        self.drawOrig()
        self.drawPair()
        self.drawBin()

    def removePairs(self):
        self.pairs = []
        self.curPairs = None
        self.drawOrig()
        self.drawPair()
        self.drawBin()

    def doGraph(self,G,labels):
        pos = Plotter.hierarchical_layout(G)
        xs = map(lambda x:pos[x][0],pos)
        ys = map(lambda x:pos[x][0],pos)
        P.axis([min(xs)-0.1,
                max(xs)+0.1,
                min(ys)-0.1,
                max(ys)+0.1])
        P.subplots_adjust(left=0,
                          right=1,
                          bottom=0,
                          top=0.9)
            
        NX.draw_networkx(G, pos, font_size=8, labels=labels, edge_color='g')
        if labels:
            for (a,b,c) in G.edges():
                # the shorter line, the closer to lower node
                ax,ay=pos[a]
                bx,by=pos[b]
                l = ((ax-bx)**2+(ay-by)**2)**0.5
                ra = 1/(l+1)
                rb = l/(l+1)
                x=(ra*ax+rb*bx)
                y=(ra*ay+rb*by)
                P.text(x,y,c.type,
                       size=8,
                       horizontalalignment='center',
                       verticalalignment='center',
                       multialignment='left')

    def drawG(self,G):
        if G.nodes():
            self.doGraph(G,Plotter.findLabels(G))
        else:
            P.axis([0,1,0,1])
            P.text(0.5,0.5,
                   "NO NODES!",
                   horizontalalignment='center',
                   verticalalignment='center',
                   size=16)
        
    def nextPairs(self):
        if not self.curPairs==None:
            cur = self.curPairs
            cur = (cur+1)%len(self.pairs)
            while not cur==self.curPairs and not self.filt(self.pairs[cur]):
                cur = (cur+1)%len(self.pairs)
            self.curPairs = cur
            self.drawPair()

    def prevPairs(self):
        if not self.curPairs==None:
            cur = self.curPairs
            cur = (cur-1)%len(self.pairs)
            while not cur==self.curPairs and not self.filt(self.pairs[cur]):
                cur = (cur-1)%len(self.pairs)
            self.curPairs = cur
            self.drawPair()
