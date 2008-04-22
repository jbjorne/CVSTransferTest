"""
The submodule corpus handles the corpus as a whole. The submodule
ontology contains and handles the BioInfer ontologies and the
submodule sentence handles individual sentences and their data. The
annotation is represented as netwrokx.XDiGraph objects.

Conversion utilities are not yet complete but new functions can easily
be added. The following guidelines must be followed to ensure the new
functions work properly:
  - always assume that input is valid
  - always check validity after any changes
  - validity includes both XSD and semantic validity
  - report any errors with printError function (error == anything that makes further processing a waste of time)
  - report any warnings with printWarning function (warning == data _might_ be corrupted by the process)
  - report any messages with printMessage function (message == information on teh status of the process; especially starts and ends of all independent parts of the process as well as any changes made into the data)
"""
