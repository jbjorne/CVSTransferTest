import sys
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import cElementTree as ET
import cElementTreeUtils as ETUtils

def recalculateIds(input, output, onlyWithinSentence=False):
    print >> sys.stderr, "##### Recalculate hierarchical interaction XML ids #####"
    print >> sys.stderr, "Loading corpus file", input
    corpusTree = ET.parse(input)
    print >> sys.stderr, "Corpus file loaded"
    corpusRoot = corpusTree.getroot()

    # Rebuild hierarchical ids
    print >> sys.stderr, "Recalculating interaction xml ids"
    corpusName = corpusRoot.attrib["source"]
    documents = corpusRoot.findall("document")
    # Recalculate ids for documents, sentences and entities
    entDictionary = {}
    docIndex = 0
    for document in documents:
        if not onlyWithinSentence:
            document.attrib["id"] = corpusName + ".d" + str(docIndex)
        sentIndex = 0
        sentences = document.findall("sentence")
        for sentence in sentences:
            if not onlyWithinSentence:
                sentence.attrib["id"] = corpusName + ".d" + str(docIndex) + ".s" + str(sentIndex)
            entIndex = 0
            entities = sentence.findall("entity")
            for entity in entities:
                if not onlyWithinSentence:
                    entNewId = corpusName + ".d" + str(docIndex) + ".s" + str(sentIndex) + ".e" + str(entIndex)
                else:
                    entNewId = sentence.attrib["id"] + ".e" + str(entIndex)
                assert not entDictionary.has_key(entity.attrib["id"]),entity.get("id")
                entDictionary[entity.attrib["id"]] = entNewId
                entity.attrib["id"] = entNewId
                entIndex += 1
            sentIndex += 1
        docIndex += 1
    # Recalculate ids for pairs and interactions
    docIndex = 0
    for document in documents:
        sentences = document.findall("sentence")
        sentIndex = 0
        for sentence in sentences:
            interactions = sentence.findall("interaction")
            intIndex = 0
            for interaction in interactions:
                if onlyWithinSentence:
                    interaction.attrib["id"] = sentence.attrib["id"] + ".i" + str(intIndex)
                else:
                    interaction.attrib["id"] = corpusName + ".d" + str(docIndex) + ".s" + str(sentIndex) + ".i" + str(intIndex)
                interaction.attrib["e1"] = entDictionary[interaction.attrib["e1"]]
                interaction.attrib["e2"] = entDictionary[interaction.attrib["e2"]]
                intIndex += 1
            pairs = sentence.findall("pair")
            pairIndex = 0
            for pair in pairs:
                if onlyWithinSentence:
                    pair.attrib["id"] = sentence.attrib["id"] + ".p" + str(pairIndex)
                else:
                    pair.attrib["id"] = corpusName + ".d" + str(docIndex) + ".s" + str(sentIndex) + ".p" + str(pairIndex)
                pair.attrib["e1"] = entDictionary[pair.attrib["e1"]]
                pair.attrib["e2"] = entDictionary[pair.attrib["e2"]]
                pairIndex += 1
            sentIndex += 1
        docIndex += 1
    
    print >> sys.stderr, "Writing output to", output
    ETUtils.write(corpusRoot, output)

if __name__=="__main__":
    import sys
    
    from optparse import OptionParser
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
        print >> sys.stderr, "Found Psyco, using"
    except ImportError:
        print >> sys.stderr, "Psyco not installed"

    defaultCorpusFilename = "BioInfer.xml"
    defaultOutputName = "BioInfer.xml"
    optparser = OptionParser(usage="%prog [options]\nPath generator.")
    optparser.add_option("-i", "--input", default=defaultCorpusFilename, dest="input", help="Corpus in interaction xml format", metavar="FILE")
    optparser.add_option("-o", "--output", default=defaultOutputName, dest="output", help="Output file in interaction xml format.")
    optparser.add_option("-s", "--sentence", action="store_true", default=False, dest="sentence", help="Only recalculate within a sentence element.")
    (options, args) = optparser.parse_args()
    
    if options.input == None:
        print >> sys.stderr, "Error, input file not defined."
        optparser.print_help()
        sys.exit(1)
    if options.output == None:
        print >> sys.stderr, "Error, output file not defined."
        optparser.print_help()
        sys.exit(1)
    
    recalculateIds(options.input, options.output, options.sentence)
