import re

class Verify:
    reId = re.compile(r'^([0-9]+):.*$')

    def __init__(self,filename):
        self.filename = filename

    def getIds(self):
        ids = set()

        id2lines = self._readLog()
        ids = set( [int(x) for x in id2lines.keys()] )
        return(ids)

    @classmethod
    def flatten(cls,id2lines):
        flat = []
        for k in sorted(id2lines.keys()):
            for line in sorted(id2lines[k]):
                flat.append(line)
        return(flat)
        
    def _readLog(self):
        logfile = open(self.filename,'r')
        id2lines = Verify._id2lines(logfile.readlines())
        logfile.close()
        return(id2lines)

    def _writeLog(self,id2lines):
        logfile = open(self.filename,'w')
        for line in Verify.flatten(id2lines):
            logfile.write("%s\n"%line)
        logfile.close()
        
    @classmethod
    def _id2lines(cls,lines):
        id2lines = {}
        for line in lines:
            match = Verify.reId.search(line.strip())
            if match:
                uid = match.groups()[0]
                if not id2lines.has_key(uid):
                    id2lines[uid] = []
                id2lines[uid].append(line.strip())
        return(id2lines)
        
    def write(self,G):
        id2lines = self._readLog()
        id2lines.update( Verify._id2lines(self.toLines([G])) )
        self._writeLog(id2lines)

    def compare(self,Gs):
        oldMap = self._readLog()
        newMap = Verify._id2lines(self.toLines(Gs))
        approvedLines = set( Verify.flatten(oldMap) )
        newLines = set( Verify.flatten(newMap) )
        approvedRemain = sorted(list(approvedLines - newLines))
        newRemain = sorted(list(newLines - approvedLines))
        return( (approvedRemain,newRemain) )

    def toLines(self,Gs):
        def sortfunc(x,y):
            if x[2].type < y[2].type:
                return(-1)
            if x[2].type > y[2].type:
                return(1)
            if x[1].token.getFull() < y[1].token.getFull():
                return(-1)
            if x[1].token.getFull() > y[1].token.getFull():
                return(1)
            return(0)
            
        lines = []
        for G in Gs:
            for root in [x for x in G.nodes() if not G.in_edges(x)]:
                string = ""
                uid = root.getSentenceId()
                string += "%s:%s"%(uid,root.token.getFull())
                for edge in sorted(G.out_edges(root),sortfunc):
                    string += ":%s-%s"%(edge[2].type,edge[1].token.getFull())
                lines.append(string)
        return(lines)
    
