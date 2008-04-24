import sys
import copy
import cElementTree as ET
from core.corpus import Corpus
from refiners import CorpusRefiner
from refiners.pack import Pack
from refiners.nesting import Nesting
from refiners.RELENT import RELENT
from refiners.EQUAL import EQUAL
from refiners.COREFER import COREFER
from refiners.NOT import NOT
from refiners.MUTUAL import MUTUAL
from utils.converter import Converter
from utils.validator import Validator
from binariser.binariser import Binariser

def process(filestem):
    new_complex = "%s.relaxed.xml"%filestem
    new_refined = "%s.refined.xml"%filestem

    corpus = Corpus()
    corpus.readFromFile(filestem)

    #CorpusRefiner(corpus,NOT).resolveAll()
    #CorpusRefiner(corpus,EQUAL).resolveAll()
    #CorpusRefiner(corpus,COREFER).resolveAll()
    #CorpusRefiner(corpus,RELENT).resolveAll()
    #CorpusRefiner(corpus,MUTUAL).resolveAll()
    CorpusRefiner(corpus,Nesting).resolveAll()
    #CorpusRefiner(corpus,Pack).resolveAll()

    corpus.writeToFile(new_refined)

    #Converter.convertFile(new_binary,old_binary,'relaxed','old')



if __name__=="__main__":
    if len(sys.argv)<2:
        print "Please specify the stem as the first argument."
        print "\t<stem>.xml == original corpus in predicate format"
        print "\t<stem>.relaxed.xml == original corpus in graph format"
        print "\t<stem>.binarised.xml == binarised corpus in predicate format"
        print "\t<stem>.binarised.relaxed.xml == binarised corpus in graph format"
    else:
        process(sys.argv[1])
