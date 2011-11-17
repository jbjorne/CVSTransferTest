import sys
from BIGraph.core.corpus import Corpus
from BIGraph.utils.plotter import Plotter

def interface(optionArgs=sys.argv[1:]):
    """
    Graphical user interface for visualising the contents of the corpus.
    The graphs are drawn with pylab package.

    @param optionArgs: command-line arguments for optparse (i.e. in the same
    format as sys.argv[1:] would contain them)
    @type  optionArgs: list

    @return: Exit status for successful run
    @rtype:  True or False
    """
    from optparse import OptionParser

    op = OptionParser(usage="%prog [options]\nPlot interaction graphs.")
    op.add_option("-s", "--source",
                  dest="source",
                  help="Source BioInfer-XML file",
                  metavar="FILE")
    op.add_option("-r", "--rules",
                  dest="rules",
                  default=None,
                  help="Rulefile for binarisation [optional]",
                  metavar="FILE")
    (options, args) = op.parse_args(optionArgs)

    quit = False
    if not options.source:
        sys.stderr.write("Please specify the source file.\n")
        quit = True
    if quit:
        return(False)

    try:
        infile = open(options.source,'r')
    except IOError, e:
        sys.stderr.write("Failed to open '%s': %s\n"%
                         (e.filename, e.strerror))
        return(False)

    a = Corpus()
    a.read(infile)
    b = Plotter(a,options.rules)

    return(True)
