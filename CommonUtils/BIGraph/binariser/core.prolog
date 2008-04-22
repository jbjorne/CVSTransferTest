:-dynamic(temp:node/6,temp:edge/5,
          temp:negated/4,temp:unnegated/4,temp:regulated/4,
          temp:root/3,temp:leaf/3,
          temp:log/3,
          rule/2,parent_child/2).

%%%% core %%%%

% find the first solution for each subgraph
transform :-
% listing(rule),
  setof(GraphId,temp:A^B^C^D^node(0,GraphId,A,B,C,D),Ids), !,
  forall(member(X,Ids),
         (
%         format('\n\n\n\n\n\nBinarising subgraph ~a\n',X),
          precalc_id(X),
          (match(0,X);true)
         )
        ),
  format("\n").

% match a version of a subgraph
match(Level,GraphId) :-
  precalc_root(Level,GraphId),
  precalc_leaf(Level,GraphId),
% format('\n\n\n\n\n\n'),
% format('Level ~a of subgraph ~a\n',[Level,GraphId]),  
% list(Level,GraphId),
  !,
  (binarised(Level,GraphId);rule(Level,GraphId)).

binarised(Level,GraphId) :-
  % match strictly binary interaction
  count_node(Level,GraphId,3),
  count_edge(Level,GraphId,2),
  temp:edge(Level,GraphId,Arun,Brun,ABtype),
  temp:edge(Level,GraphId,Arun,Crun,ACtype),
  Brun \== Crun,
  ( (ABtype==agent,ACtype==patient);
    (ABtype==patient,ACtype==agent);
    (ABtype==agpat,ACtype==agpat)
  ),
  temp:node(Level,GraphId,Brun,Bid,Btype,Bnested),
  temp:node(Level,GraphId,Crun,Cid,Ctype,Cnested),
  (Btype\==Ctype;Bnested\==Cnested),
  compare(<,Bid,Cid), !,
%   % adjust for regulation in root node
%   % (enable if consistent treatment of regulatory predicates is desired)
%   adjust_root_regulation(Level,GraphId,Arun),
  % produce output
  temp:node(Level,GraphId,Arun,Aid,Atype,Anested),
  flag(counter_results,BinaryRunId,BinaryRunId+1),
  concat_atom([Bid,Cid],'&',PairId),
  % concatenate regulation to type
  (temp:regulated(Level,GraphId,REGdir,REGnested)
  -> ( (REGdir =:= 1, atom_concat('REG(+)_',Atype,TmpString));
       (REGdir =:= 0, atom_concat('REG(0)_',Atype,TmpString));
       (REGdir =:= -1, atom_concat('REG(-)_',Atype,TmpString));
       atom_concat('ACTION_',Atype,TmpString) )
  ; (REGnested = [],
     atom_concat('ACTION_',Atype,TmpString))
  ),
  % concatenate negation to type
  ( (temp:negated(Level,GraphId,Arun,NOTnested),
     atom_concat('NEG_',TmpString,FinalAtype));
    (temp:unnegated(Level,GraphId,Arun,NOTnested),
     atom_concat('POS_',TmpString,FinalAtype));
    (NOTnested = [],
     atom_concat('POS_',TmpString,FinalAtype))
  ),
  flatten([Anested,NOTnested,REGnested],Flat),
  sort(Flat,FinalAnested),
  concat_atom(FinalAnested,'-',Astring),
  concat_atom(Bnested,'-',Bstring),
  concat_atom(Cnested,'-',Cstring),
  forall(temp:log(_,GraphId,LogText),format('~a\n',LogText)),
  format('~a:~a:~a:~a:node(~a,~a,~a,~a)\n',
         [BinaryRunId,GraphId,PairId,Level,Arun,Aid,FinalAtype,Astring]),
  format('~a:~a:~a:~a:node(~a,~a,~a,~a)\n',
         [BinaryRunId,GraphId,PairId,Level,Brun,Bid,Btype,Bstring]),
  format('~a:~a:~a:~a:node(~a,~a,~a,~a)\n',
         [BinaryRunId,GraphId,PairId,Level,Crun,Cid,Ctype,Cstring]),
  format('~a:~a:~a:~a:edge(~a,~a,~a)\n',
         [BinaryRunId,GraphId,PairId,Level,Arun,Brun,ABtype]),
  format('~a:~a:~a:~a:edge(~a,~a,~a)\n',
         [BinaryRunId,GraphId,PairId,Level,Arun,Crun,ACtype]).

adjust_root_regulation(Level,GraphId,Arun) :-
  nodetype_regulation(Level,GraphId,Arun),
  regulate(Level,GraphId,Arun),
  set_nodetype(Level,GraphId,Arun,'Dynamics').
adjust_root_regulation(Level,GraphId,Arun) :-
  true.

precalc_id(GraphId) :-
  temp:node(Level,GraphId,Rrun,Root,_,_),
  \+temp:edge(Level,GraphId,_,Rrun,_),
  findall(Leaf,
          (
           temp:node(Level,GraphId,Lrun,Leaf,Ltype,_),
           \+temp:edge(Level,GraphId,Lrun,_,_),
           Ltype \== 'NOT'
          ),
          Leafs
         ),
  sort(Leafs,LeafsSorted),
  flatten([[Root],LeafsSorted],Flat),
  concat_atom(Flat,'-',Full),
  assert(temp:logid(GraphId,Full)).

precalc_root(Level,GraphId) :-
  retractall(temp:root(Level,GraphId,_)),
  temp:node(Level,GraphId,Arun,_,_,_),
  \+temp:edge(Level,GraphId,_,Arun,_),
  assert(temp:root(Level,GraphId,Arun)).

precalc_leaf(Level,GraphId) :-
  retractall(temp:leaf(Level,GraphId,_)),
  forall(
         (
          temp:node(Level,GraphId,Arun,_,_,_),
          \+temp:edge(Level,GraphId,Arun,_,_)
         ),
         assert(temp:leaf(Level,GraphId,Arun))
        ).

count_node(Level,GraphId,Count) :-
  findall(-,clause(temp:node(Level,GraphId,_,_,_,_),_),List),
  length(List,Count).

count_edge(Level,GraphId,Count) :-
  findall(-,clause(temp:edge(Level,GraphId,_,_,_),_),List),
  length(List,Count).

prepare_level(Level,GraphId,NewLevel) :-
  plus(Level,1,NewLevel),
  retractall(temp:node(NewLevel,GraphId,_,_,_,_)),
  retractall(temp:edge(NewLevel,GraphId,_,_,_)),
  retractall(temp:negated(NewLevel,GraphId,_,_)),
  retractall(temp:unnegated(NewLevel,GraphId,_,_)),
  retractall(temp:regulated(NewLevel,GraphId,_,_)),
  forall(temp:node(Level,GraphId,Arun,Aid,Atype,Anested),
         assert(temp:node(NewLevel,GraphId,Arun,Aid,Atype,Anested))),
  forall(temp:edge(Level,GraphId,Arun,Brun,ABtype),
         assert(temp:edge(NewLevel,GraphId,Arun,Brun,ABtype))),
  forall(temp:negated(Level,GraphId,Arun,Anested),
         assert(temp:negated(NewLevel,GraphId,Arun,Anested))),
  forall(temp:unnegated(Level,GraphId,Arun,Anested),
         assert(temp:unnegated(NewLevel,GraphId,Arun,Anested))),
  forall(temp:regulated(Level,GraphId,Arun,Anested),
         assert(temp:regulated(NewLevel,GraphId,Arun,Anested))).

different_nodes([]) :-
        true.
different_nodes([H|T]) :-
        forall(member(X,T), H\==X),
        different_nodes(T).

log_match(Level,GraphId,Text) :-
  temp:logid(GraphId,Id),
  concat_atom(['matched(',Id,',',Text,')'],'',String),
  retractall(temp:log(Level,GraphId,_)),
  assert(temp:log(Level,GraphId,String)).


%%%% debug %%%%

list(Level,GraphId,_) :-
  list(Level,GraphId).
list(Level,GraphId) :-
  listing(temp:root(Level,GraphId,_)),
  listing(temp:leaf(Level,GraphId,_)),
  listing(temp:node(Level,GraphId,_,_,_,_)),
  listing(temp:edge(Level,GraphId,_,_,_)),
  listing(temp:negated(Level,GraphId,_,_)),
  listing(temp:unnegated(Level,GraphId,_,_)),
  listing(temp:regulated(Level,GraphId,_,_)),
  format('\n').

print_try(Level,GraphId,Text):-
  format('Try ~a at level ~a of subgraph ~a\n',[Text,Level,GraphId]).

print_match(Level,GraphId,Text):-
  format('Matched ~a in subgraph ~a - next level ~a\n',[Text,GraphId,Level]).

print_var(Level,GraphId,Arun):-
  temp:node(Level,GraphId,Arun,Aid,Atype,_),
  format('~a = ~a : ~a\n',[Arun,Aid,Atype]).
