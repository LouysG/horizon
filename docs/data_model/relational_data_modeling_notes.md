# Relational Data Modeling Notes
For a while now I've had trouble grokking relational data modeling. 

I think the reason is that I think of data as representing Reality which I see as structured according to an Ontology. Object-oriented programming rewards this mindset. Lowercase 'r' realities are instantiated by creating an object-model which is essentially a taxonomy of the kinds of object which can exist within a program. Then, at runtime one simply instantiates an object.

Relational data modeling does not reward the ontological mindset. Relational data modeling is an application of predicate logic. It does not ask "What kind of thing is this and where does it belong in the hierarchy of things?", instead it asks, "What propositions about the world do I need to represent as data?". 

Object-oriented programming concerns itself with objects, relational data modeling concerns itself with facts.

## Predicate Logic

### Predicates
A predicate is a function that expresses the property of an object or a relationship between objects.

Examples:
- P(x) : x is prime
- C(x, y) : x contains y  

### Variables
Symbols such as x, y, and z that act as placeholders for unspecified objects in a domain.

### Logical Operators
Various symbols from propositional logic:

- $\lnot$ : Negation
- $\land$ : Conjunction
- $\lor$ : Disjunction 
- $\Rightarrow$ : Implication

### Quantifiers
Operators that specify how many members of a domain satisfy a predicate.

- $\forall$x : The universal quantifier. Exaluates to true if all members of the domain satisfy the quantified predicated.
- $\exists$x : The existential quantifier. Evaluates to true if one member of a domain satisfies the quantified predicate.


## Foundational Relational Data Modeling Design Patterns

### Design Patterns
| Pattern | Description | Implementation |
| --- | --- | --- |
| Entity and attributes | A thing exists and has properties | Table w/ primary key
| One-to-many | One A relates to many B's; Each B relates to at most one A | Foreign key
| Many-to-many | Many A's relate to many B's | Junction table
| One-to-one | One A relates to at most one B | Unique foreign key
| Subtype | Every B is a kind of A | Type discriminator or subtype table
| Recursive relationship | Entities of the same type relate to one another | Self-referencing foreign key or junction table
| Associative entity | A relationship has its own attributes or identity | Junction table with additional columns
| Weak Entity | An entity's existence depends on another entity | Foreign key, often part of a composite primary key |
| Lookup Table | A controlled set of values represented as reusable records | Reference table with foreign keys |
| Temporal Records | Facts or relationships are recorded across time | timestamped or effective-dated records |

## Levels of Abstraction

- Relational Design Patterns
- Data Modeling Methodologies
- Methodology-Specific Patterns


