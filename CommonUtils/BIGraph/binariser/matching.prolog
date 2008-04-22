%%%% rule-related actions %%%%

terminate(Level,GraphId,Arun) :-
  retractall(temp:node(Level,GraphId,_,_,_,_)),
  retractall(temp:edge(Level,GraphId,_,_,_)).

print_log(Level,GraphId,Arun) :-
  forall(temp:log(_,GraphId,LogText),format('~a\n',LogText)).

remove_node(Level,GraphId,Arun) :-
  retractall(temp:node(Level,GraphId,Arun,_,_,_)).

negate(Level,GraphId,Arun,NOTrun) :-
  temp:node(Level,GraphId,NOTrun,_,_,NOTnew),
  ( (temp:negated(Level,GraphId,Arun,NOTold), Old = -1);
    (temp:unnegated(Level,GraphId,Arun,NOTold), Old = 1);
    (NOTold = [], Old = 1)
  ),
  union(NOTold,NOTnew,Joined),
  ( Old =:= -1
  -> (retractall(temp:negated(Level,GraphId,Arun,_)),
      assert(temp:unnegated(Level,GraphId,Arun,Joined)))
  ; (retractall(temp:unnegated(Level,GraphId,Arun,_)),
     assert(temp:negated(Level,GraphId,Arun,Joined)))
  ).

negate_add(Level,GraphId,Arun,Brun) :-
  ( (temp:negated(Level,GraphId,Arun,Anested), Apos = -1);
    (temp:unnegated(Level,GraphId,Arun,Anested), Apos = 1);
    (Anested = [], Apos = 1)
  ),
  ( (temp:negated(Level,GraphId,Brun,Bnested), Bpos = -1);
    (temp:unnegated(Level,GraphId,Brun,Bnested), Bpos = 1);
    (Bnested = [], Bpos = 1)
  ),
  union(Anested,Bnested,Joined),
  Ndir is Apos * Bpos,
  retractall(temp:negated(Level,GraphId,Arun,_)),
  retractall(temp:unnegated(Level,GraphId,Arun,_)),
  ( (Ndir =:= -1, assert(temp:negated(Level,GraphId,Arun,Joined)));
    (Ndir =:= 1, length(Joined,0));
    (Ndir =:= 1, assert(temp:unnegated(Level,GraphId,Arun,Joined)))
  ).

regulate(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Atype,Anested),
  ( (regulation_positive(Atype), Adir = 1);
    (regulation_unspecified(Atype), Adir = 0);
    (regulation_negative(Atype), Adir = -1)
  ),
  ( (temp:negated(Level,GraphId,Arun,NOTnested), NOTdir = -1);
    (temp:unnegated(Level,GraphId,Arun,NOTnested), NOTdir = 1);
    (NOTnested = [], NOTdir = 1)
  ),
  ( (temp:regulated(Level,GraphId,REGdir,REGnested),
     (REGdir =:= 1; REGdir =:= 0; REGdir =:= -1))
  -> (Ndir is Adir * REGdir * NOTdir,
      flatten([Anested,REGnested,NOTnested],Flat))
  ; (Ndir is Adir * NOTdir, % ACTION-reg or no prior regulation
     flatten([Anested,NOTnested],Flat))
  ),
  sort(Flat,Nnested),
  retractall(temp:regulated(Level,GraphId,_,_)),
  assert(temp:regulated(Level,GraphId,Ndir,Nnested)).

regulate(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Atype,Anested),
  Adir = 9, % ACTION-reg (recessive to real regulation)
  % negations do not influence the ACTION-reg status
  ( temp:regulated(Level,GraphId,REGdir,REGnested)
  -> ( (REGdir =:= 1; REGdir =:= 0; REGdir =:= -1)
     % real regulation present -> do nothing
     -> (true)
     % ACTION-regulation present -> merge tokens
     ; (flatten([Anested,REGnested],Flat),
        sort(Flat,Nnested),
        retractall(temp:regulated(Level,GraphId,_,_)),
        assert(temp:regulated(Level,GraphId,Adir,Nnested))
       )
     )
  % no regulation present -> new regulation
  ; (assert(temp:regulated(Level,GraphId,Adir,Anested)))
  ).

set_nodetype(Level,GraphId,Arun,NewType) :-
  forall(temp:node(Level,GraphId,Arun,Aid,Atype,Anested),
         (retract(temp:node(Level,GraphId,Arun,Aid,Atype,Anested)),
          assert(temp:node(Level,GraphId,Arun,Aid,NewType,Anested)))).

set_nodetype_parent(Level,GraphId,Arun,Brun) :-
  temp:node(Level,GraphId,Brun,_,Type,_),
  parent_child(Parent,Type),
  set_nodetype(Level,GraphId,Arun,Parent).

set_nodetype_change(Level,GraphId,Arun,Brun) :-
  temp:node(Level,GraphId,Brun,_,Type,_),
  below(Type,Property),
  property_change(Property,Change),
  set_nodetype(Level,GraphId,Arun,Change).

map_edges(Level,GraphId,FromRun,ToRun) :-
  forall(temp:edge(Level,GraphId,Arun,FromRun,ABtype),
         (retract(temp:edge(Level,GraphId,Arun,FromRun,ABtype)),
          assert(temp:edge(Level,GraphId,Arun,ToRun,ABtype)))),
  forall(temp:edge(Level,GraphId,FromRun,Brun,ABtype),
         (retract(temp:edge(Level,GraphId,FromRun,Brun,ABtype)),
          assert(temp:edge(Level,GraphId,ToRun,Brun,ABtype)))),
  retractall(temp:node(Level,GraphId,FromRun,_,_,_)).

nested_add(Level,GraphId,Arun,Brun) :-
  temp:node(Level,GraphId,Arun,_,_,Anested),
  temp:node(Level,GraphId,Brun,_,_,Bnested),
  union(Anested,Bnested,Joined),
  nested_set(Level,GraphId,Arun,Joined).  

nested_set(Level,GraphId,Arun,NewNested) :-
  forall(temp:node(Level,GraphId,Arun,Aid,Atype,Anested),
         (retract(temp:node(Level,GraphId,Arun,Aid,Atype,Anested)),
          assert(temp:node(Level,GraphId,Arun,Aid,Atype,NewNested)))).

%%%% rule-related restrictions %%%%

leaf(Level,GraphId,Arun) :-
  temp:leaf(Level,GraphId,Arun).

root(Level,GraphId,Arun) :-
  temp:root(Level,GraphId,Arun).

negated(Level,GraphId,Arun) :-
  temp:negated(Level,GraphId,Arun,_).

nodetype(Level,GraphId,Arun,Type) :-
  temp:node(Level,GraphId,Arun,_,Type,_).

nodetype_regulation(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  regulation(Type).

% nodetype_regulation_positive(Level,GraphId,Arun) :-
%   temp:node(Level,GraphId,Arun,_,Type,_),
%   regulation_positive(Type).

% nodetype_regulation_negative(Level,GraphId,Arun) :-
%   temp:node(Level,GraphId,Arun,_,Type,_),
%   regulation_negative(Type).

% nodetype_regulation_unspecified(Level,GraphId,Arun) :-
%   temp:node(Level,GraphId,Arun,_,Type,_),
%   regulation_unspecified(Type).

nodetype_action(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  action(Type).
  
nodetype_physical(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  tripletype(Type,'Physical').
  
nodetype_process(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  tripletype(Type,'Process').

nodetype_property(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  tripletype(Type,'Property').

nodetype_symmetric(Level,GraphId,Arun) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  symmetric(Type).

nodetype_effect(Level,GraphId,Arun,Effect) :-
  temp:node(Level,GraphId,Arun,_,Type,_),
  process_effect(Type,Effect).

nodetype_below(Level,GraphId,Arun,Type) :-
  temp:node(Level,GraphId,Arun,_,X,_),
  below(X,Type).

%%%% helper predicates %%%%

regulation(Type) :-
  regulation_positive(Type);
  regulation_negative(Type);
  regulation_unspecified(Type).

regulation_positive(Type) :-
  (below(Type,'Positive'), Type \== 'MEDIATE');
  below(Type,'Start');
  Type == 'INCREASE'.

regulation_negative(Type) :-
  below(Type,'Negative');
  below(Type,'Full-Stop');
  Type == 'DECREASE';
  Type == 'PREVENT'.

regulation_unspecified(Type) :-
  Type == 'Amount';
  Type == 'AFFECT';
  below(Type,'Unspecified').

action(Type) :-
  Type == 'MEDIATE';
  Type == 'CAUSE';
  Type == 'CONDITION';
  Type == 'PARTICIPATE'.

above(Type,Target) :- Type = Target.
above(Type,Target) :- parent_child(Type,Target).
above(Type,Target) :- parent_child(Middle,Target),above(Type,Middle).

below(Type,Target) :- Type = Target.
below(Type,Target) :- parent_child(Target,Type).
below(Type,Target) :- parent_child(Middle,Type),below(Middle,Target).

% NOTE: these should be embedded to the relentityvocabulary
property_change('Location_property','Location').
property_change('Amount_property','Amount').
property_change('Physical_property','Physical').
property_change('Dynamics_property','Dynamics').
% Function_property does not have specific predicate under Dynamics
property_change('Property_entity','Change').
