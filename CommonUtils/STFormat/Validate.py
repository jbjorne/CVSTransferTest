def validateREL(documents):
    for document in documents:
        if len(document.events) > 0:
            print >> sys.stderr, "Warning, events for REL task"
        for relation in relations:
            assert len(relation.arguments) == 2
            pass

def compareEvents(e1, e2):
    if e1.type == e2.type and e1.trigger == e2.trigger and len(e1.arguments) == len(e2.arguments):
        for arg1, arg2 in zip(e1.arguments, e2.arguments):
            if arg1[0] != arg2[0] or arg1[1] != arg2[1] or arg1[2] != arg2[2]:
                return False
        return True
    else:
        return False

def removeDuplicates(events):
    numRemoved = 1
    totalRemoved = 0
    # Since removed events cause nesting events' arguments to be remapped, 
    # some of these nesting events may in turn become duplicates. Loop until
    # all such duplicates are removed.
    while(numRemoved > 0):
        # Group duplicate events
        duplGroups = {}
        isDuplicate = {}
        for i in range(len(events)-1):
            e1 = events[i]
            duplGroups[e1] = [] # "same as e1"
            # Check all other events against e1
            for j in range(i+1, len(events)):
                e2 = events[j]
                if compareEvents(e1, e2):
                    if e2 not in isDuplicate: # else already added to a duplGroup
                        isDuplicate[e2] = True
                        duplGroups[e1].append(e2)
        # Mark events for keeping or removal
        replaceWith = {}
        toRemove = set()
        for mainEvent, duplGroup in duplGroups.iteritems():
            if len(duplGroup) == 0:
                continue
            # Mark for removal or preservation
            for event in duplGroup:
                assert event not in replaceWith
                replaceWith[event] = mainEvent
                toRemove.add(event)    
        # Remove events and remap arguments
        kept = []
        for event in events:
            if event not in toRemove:
                for arg in event.arguments:
                    if arg[1] in replaceWith:
                        assert arg[2] == None
                        arg[1] = replaceWith[arg[1]]
                kept.append(event)
        numRemoved = len(events) - len(kept)
        totalRemoved += numRemoved
        events = kept
    return events

def getBISuperType(eType):
    if eType in ["GeneProduct", "Protein", "ProteinFamily", "PolymeraseComplex"]:
        return "ProteinEntity"
    elif eType in ["Gene", "GeneFamily", "GeneComplex", "Regulon", "Site", "Promoter"]:
        return "GeneEntity"
    else:
        return None
        
# Enforce type-specific limits
def validate(events, simulation=False, verbose=False, docId=None):
    numRemoved = 1
    totalRemoved = 0
    if simulation:
        verbose = True
    docId = str(docId)
    # Since removed events cause nesting events' arguments to be remapped, 
    # some of these nesting events may in turn become duplicates. Loop until
    # all such duplicates are removed.
    while(numRemoved > 0):
        toRemove = set()
        for event in events:
            # Check arguments
            for arg in event.arguments[:]:
                #if arg[1].type == "Entity":
                #    print "arg[1] == Entity"
                #    if not verbose:
                #        assert False, arg
                if arg[2] != None and arg[2].type != "Entity":
                    print "arg[2] != Entity:", arg[2].type
                    if not verbose:
                        assert False, arg
            # GE-regulation rules
            if "egulation" in event.type:
                typeCounts = {"Cause":0, "Theme":0}
                for arg in event.arguments[:]:
                    if arg[0] not in typeCounts:
                        event.arguments.remove(arg)
                    else:
                        typeCounts[arg[0]] += 1
                if typeCounts["Theme"] == 0:
                    toRemove.add(event)
                    if verbose: print "VAL:", docId + "." + str(event.id), "(P/N/R)egulation with no themes"
                if len(event.arguments) == 0:
                    toRemove.add(event)
                    if verbose: print "VAL:", docId + "." + str(event.id), "(P/N/R)egulation with no arguments"
            # Remove illegal arguments (GE=Only a protein can be a Theme for a non-regulation event)
            if event.type in ["Gene_expression", "Transcription"]:
                for arg in event.arguments[:]:
                    if arg[0] == "Theme" and arg[1].type not in ["Protein", "Regulon-operon"]:
                        event.arguments.remove(arg)
                        if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with", arg[0], "arg of type", arg[1].type
            if event.type in ["Protein_catabolism", "Phosphorylation"]:
                for arg in event.arguments[:]:
                    if arg[0] == "Theme" and arg[1].type not in ["Protein"]:
                        event.arguments.remove(arg)
                        if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with", arg[0], "arg of type", arg[1].type
            if event.type in ["Localization", "Binding"]:
                for arg in event.arguments[:]:
                    if arg[0] == "Theme" and arg[1].type not in ["Protein", "Regulon-operon", "Two-component-system", "Chemical", "Organism"]:
                        event.arguments.remove(arg)          
                        if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with", arg[0], "arg of type", arg[1].type
            # Check non-regulation events
            if event.type in ["Gene_expression", "Transcription", "Protein_catabolism", "Phosphorylation", "Localization", "Binding"]:
                themeCount = 0
                for arg in event.arguments:
                    if arg[0] == "Theme":
                        themeCount += 1
                if themeCount == 0:
                    if event.type == "Localization" and len(event.arguments) > 0: # Also used in BB
                        for arg in event.arguments:
                            if arg[0] in ["ToLoc", "AtLoc"]: # GE-task Localization
                                if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with no themes"
                                toRemove.add(event)
                                break
                    else:
                        toRemove.add(event)
                        if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with no themes"
            # check non-binding events
            if event.type != "Binding":
                themeCount = 0
                for arg in event.arguments:
                    if arg[0] == "Theme":
                        themeCount += 1
                if themeCount > 1:
                    toRemove.add(event)
                    if verbose: print "VAL:", docId + "." + str(event.id), "Non-binding event", event.type, "with", themeCount, "themes"
            if event.type == "PartOf": # BB
                assert len(event.arguments) == 2
                # BB
                if event.arguments[0][1].type != "Host":
                    toRemove.add(event)
                    if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with arg 1 of type", event.arguments[0][1].type
                if event.arguments[1][1].type != "HostPart":
                    toRemove.add(event)
                    if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with arg 2 of type", event.arguments[1][1].type
            if event.type == "Localization": # BB and others
                for arg in event.arguments:
                    if arg[0] == "Bacterium" and arg[1].type != "Bacterium":
                        if verbose: print "VAL:", docId + "." + str(event.id), event.type, "with", arg[0], "arg of type", arg[1].type
                        toRemove.add(event)
            
            # BI-rules
            if len(event.arguments) == 2:
                arg1Type = event.arguments[0][1].type
                arg1SuperType = getBISuperType(arg1Type)
                arg2Type = event.arguments[1][1].type
                arg2SuperType = getBISuperType(arg2Type)
            if event.type == "RegulonDependence":
                if arg1Type != "Regulon": toRemove.add(event)
                if arg2SuperType not in ["GeneEntity", "ProteinEntity"]: toRemove.add(event)
            elif event.type == "BindTo":
                if arg1SuperType != "ProteinEntity": toRemove.add(event)
                if arg2Type not in ["Site", "Promoter", "Gene", "GeneComplex"]: toRemove.add(event)
            elif event.type == "TranscriptionFrom":
                if arg1Type not in ["Transcription", "Expression"]: toRemove.add(event)
                if arg2Type not in ["Site", "Promoter"]: toRemove.add(event)
            elif event.type == "RegulonMember":
                if arg1Type != "Regulon": toRemove.add(event)
                if arg2SuperType not in ["GeneEntity", "ProteinEntity"]: toRemove.add(event)
            elif event.type == "SiteOf":
                if arg1Type != "Site": toRemove.add(event)
                if not (arg2Type in ["Site", "Promoter"] or arg2SuperType == "GeneEntity"): toRemove.add(event)
            elif event.type == "TranscriptionBy":
                if arg1Type != "Transcription": toRemove.add(event)
                if arg2SuperType != "ProteinEntity": toRemove.add(event)
            elif event.type == "PromoterOf":
                if arg1Type != "Promoter": toRemove.add(event)
                if arg2SuperType not in ["ProteinEntity", "GeneEntity"]: toRemove.add(event)
            elif event.type == "PromoterDependence":
                if arg1Type != "Promoter": toRemove.add(event)
                if arg2SuperType not in ["ProteinEntity", "GeneEntity"]: toRemove.add(event)
            elif event.type == "ActionTarget":
                if arg1Type not in ["Action", "Expression", "Transcription"]: toRemove.add(event)
            elif event.type == "Interaction":
                if arg1SuperType not in ["ProteinEntity", "GeneEntity"]: toRemove.add(event)
                if arg2SuperType not in ["ProteinEntity", "GeneEntity"]: toRemove.add(event)
            # BI-task implicit rules (not defined in documentation, discovered by evaluator complaining)
            if len(event.arguments) == 2:
                # Evaluator says: "SEVERE: role Target does not allow entity of type Site".
                # This is not actually true, because if you check this for all Target-arguments, and
                # remove such events, performance decreases for the gold-data. But what can you do,
                # the evaluator keeps complaining, and won't process the data. The "solution" is to 
                # remove from Target/Site-checking those classes which reduce performance on gold data.
                if event.type not in ["BindTo", "SiteOf"]:
                    if arg1Type == "Site" and event.arguments[0][0] == "Target": toRemove.add(event)
                    if arg2Type == "Site" and event.arguments[1][0] == "Target": toRemove.add(event)
                    
        # Remove events and remap arguments
        if not simulation:
            kept = []
            for event in events:
                if event not in toRemove:
                    for arg in event.arguments[:]:
                        if arg[1] in toRemove:
                            event.arguments.remove(arg)
                    kept.append(event)
            numRemoved = len(events) - len(kept)
            totalRemoved += numRemoved
            events = kept
        else:
            numRemoved = 0
    return events

def removeUnusedTriggers(document):
    # Remove triggers which are not used as triggers or arguments
    triggersToKeep = []
    for trigger in document.triggers:
        kept = False
        for event in document.events:
            if event.trigger == trigger:
                triggersToKeep.append(trigger)
                kept = True
                break
            else:
                for arg in event.arguments:
                    if arg[1] == trigger or arg[2] == trigger:
                        triggersToKeep.append(trigger)
                        kept = True
                        break
            if kept:
                break
    document.triggers = triggersToKeep

def allValidate(document, counts, task, verbose=False):
    numEvents = len(document.events)
    document.events = validate(document.events, verbose=verbose, docId=document.id)
    counts["validation-removed"] += numEvents - len(document.events)
    numEvents = len(document.events)
    document.events = removeDuplicates(document.events)
    counts["duplicates-removed"] += numEvents - len(document.events)
    removeArguments(document, task, counts)
    removeEntities(document, task, counts)
    # triggers
    numTriggers = len(document.triggers)
    removeUnusedTriggers(document)
    counts["unused-triggers-removed"] += numTriggers - len(document.triggers)

def removeArguments(document, task, counts):
    if task != 1:
        return
    for event in document.events:
        for arg in event.arguments[:]:
            if arg[0] in ["Site", "AtLoc", "ToLoc"]:
                event.arguments.remove(arg)
                counts["t2-arguments-removed"] += 1
    
def removeEntities(document, task, counts):
    if task != 1:
        return
    # "Entity"-entities are not used in task 1, so they
    # can be removed then.
    triggersToKeep = []
    for trigger in document.triggers:
        if trigger.type == "Entity":
            counts["t2-entities-removed"] += 1
        else:
            triggersToKeep.append(trigger)
    document.triggers = triggersToKeep
            