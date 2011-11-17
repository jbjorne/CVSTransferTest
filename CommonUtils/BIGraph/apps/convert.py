import sys
import inspect
import cElementTree as ET
from BIGraph.utils.converter import Converter
from BIGraph import *

def interface(optionArgs=sys.argv[1:]):
    """
    Command-line interface for converting BioInfer XML files between
    different formats.

    @param optionArgs: command-line arguments for optparse (i.e. in the same
    format as sys.argv[1:] would contain them)
    @type  optionArgs: list

    @return: boolean for a successful run
    @rtype:  True or False
    """
    from optparse import OptionParser

    op = OptionParser(usage="%prog [options]\nConvert BioInfer XML files between different formats.")
    op.add_option("-s", "--source",
                  dest="source",
                  help="Source BioInfer-XML file",
                  metavar="FILE")
    op.add_option("-t", "--target",
                  dest="target",
                  help="Target BioInfer-XML file",
                  metavar="FILE")
    op.add_option("--sf", "--sourceformat",
                  dest="sourceformat",
                  help="Format of source file",
                  action="store",
                  default="old",
                  type="choice",
                  choices=['old','new','relaxed','compatible'],
                  metavar='[old|new|relaxed|[compatible]')
    op.add_option("--tf", "--targetformat",
                  dest="targetformat",
                  help="Format of target file",
                  action="store",
                  default="new",
                  type="choice",
                  choices=['old','new','relaxed','compatible'],
                  metavar='[old|new|relaxed|[compatible]')
    (options, args) = op.parse_args(optionArgs)

    quit = False
    if not options.source:
        printError('Convert',inspect.stack()[0][3],
                   "Please specify the source file.")
        quit = True
    if not options.target:
        printError('Convert',inspect.stack()[0][3],
                   "Please specify the target file.")
        quit = True
    if quit:
        op.print_help()
        return(False)
   
    printMessage('Convert',inspect.stack()[0][3],
                 "Converting from %s to %s.."%(options.sourceformat,
                                               options.targetformat))
    Converter.convertFile(options.source,
                          options.target,
                          options.sourceformat,
                          options.targetformat)
    printMessage('Convert',inspect.stack()[0][3],"Converted")
    return(True)
