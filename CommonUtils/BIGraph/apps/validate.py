import sys
import os
import inspect
from BIGraph import *
from BIGraph.utils.validator import Validator

def interface(optionArgs=sys.argv[1:]):
    """
    Command-line interface for validating BioInfer XML. Both XSD
    validation and semantic validation are performed.

    @param optionArgs: command-line arguments for optparse (i.e. in the same
    format as sys.argv[1:] would contain them)
    @type  optionArgs: list

    @return: boolean for valid XML
    @rtype:  True or False
    """
    from optparse import OptionParser

    op = OptionParser(usage="%prog [options]\nValidate BioInfer XML (XSD and semantic).")
    op.add_option("-s", "--source",
                  dest="source",
                  help="BioInfer XML file",
                  metavar="FILE")
    op.add_option("-f", "--format",
                  dest="format",
                  action="store",
                  default="new",
                  type="choice",
                  choices=['new','relaxed','compatible'],
                  metavar='[new|relaxed|[compatible]',
                  help="Which format to validate against?")
    (options, args) = op.parse_args(optionArgs)

    quit = False
    if not options.source:
        printError('Validate',inspect.stack()[0][3],
                   "Please specify the source file.")
        quit = True
    if quit:
        op.print_help()
        return(False)

    printMessage('Validate',inspect.stack()[0][3],
                 "Validating %s.."%(options.source))
    valid = Validator.validateFromFile(options.source,options.format)
    printMessage('Validate',inspect.stack()[0][3],
                 "Validated")
    return(valid)
