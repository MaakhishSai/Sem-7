# 3-SAT Problem: Comprehensive Algorithm Guide

## Overview
This document provides complete implementations and explanations for solving the 3-SAT problem using different search algorithms and heuristics.

## Problem Definition
3-SAT (3-Satisfiability) is the problem of determining whether a Boolean formula in 3-CNF (Conjunctive Normal Form with 3 literals per clause) can be satisfied.

### Example Formula:
```
(x₁ ∨ x₂ ∨ x₃) ∧ (¬x₁ ∨ x₂ ∨ x₃) ∧ (¬x₁ ∨ ¬x₂ ∨ ¬x₃) ∧ (x₁ ∨ ¬x₂ ∨ x₃)
```

## Algorithms Implemented

### 1. Breadth-First Search (BFS)
- **Type**: Uninformed search
- **Space Complexity**: O(b^d)
- **Time Complexity**: O(b^d)
- **Complete**: Yes
- **Optimal**: Yes (for unit cost)

### 2. Depth-First Search (DFS)
- **Type**: Uninformed search
- **Space Complexity**: O(bd)
- **Time Complexity**: O(b^m)
- **Complete**: No (with cycles)
- **Optimal**: No

### 3. Iterative Deepening DFS (IDFS)
- **Type**: Uninformed search
- **Space Complexity**: O(bd)
- **Time Complexity**: O(b^d)
- **Complete**: Yes
- **Optimal**: Yes (for unit cost)

### 4. Hill Climbing
- **Type**: Local search
- **Space Complexity**: O(1)
- **Time Complexity**: Variable
- **Complete**: No
- **Optimal**: No

### 5. Best First Search
- **Type**: Informed search
- **Space Complexity**: O(b^d)
- **Time Complexity**: O(b^m)
- **Complete**: No (general), Yes (with graph search)
- **Optimal**: No

### 6. A* Algorithm
- **Type**: Informed search
- **Space Complexity**: O(b^d)
- **Time Complexity**: O(b^d)
- **Complete**: Yes (with admissible heuristic)
- **Optimal**: Yes (with admissible heuristic)

## Heuristics for 3-SAT

### 1. Unsatisfied Clauses Heuristic
**Description**: Count how many unsatisfied clauses each variable appears in.
**Formula**: h(var) = Σ(var ∈ unsatisfied_clause)
**Properties**: 
- Not admissible (can overestimate)
- Good for guiding search toward constraint satisfaction

### 2. Jeroslow-Wang Heuristic
**Description**: Weight variables by clause length using exponential decay.
**Formula**: h(var) = Σ(2^(-|clause|)) for all clauses containing var
**Properties**:
- Emphasizes variables in shorter clauses
- Based on resolution theorem proving

### 3. Most Constraining Variable (MCV)
**Description**: Choose variable appearing in most unsatisfied clauses.
**Formula**: h(var) = |{clauses | var ∈ clause ∧ clause is unsatisfied}|
**Properties**:
- Fails-first principle
- Reduces branching factor early

### 4. Unit Propagation Heuristic
**Description**: Prioritize variables in unit clauses (clauses with only one unassigned literal).
**Formula**: h(var) = 10 if var is in unit clause, else 0
**Properties**:
- Forces immediate assignments
- Maintains arc consistency

### 5. Backbone Heuristic
**Description**: Variables that appear with consistent polarity across unsatisfied clauses.
**Formula**: h(var) = max(positive_count, negative_count) / total_occurrences
**Properties**:
- Identifies structural constraints
- Good for hard instances

### 6. Combined A* Heuristic
**Description**: Combination of Manhattan distance and unsatisfied clauses.
**Formula**: h(state) = (num_vars - assigned_vars) + unsatisfied_clauses
**Properties**:
- Admissible lower bound component
- Problem-specific guidance

## Performance Comparison

Based on test results:

### Simple Formula (3 variables, 4 clauses):
| Algorithm | Nodes Explored | Time (ms) | Satisfiable |
|-----------|----------------|-----------|-------------|
| BFS | 9 | 0.18 | Yes |
| DFS | 5 | 0.04 | Yes |
| IDFS | 15 | 0.09 | Yes |
| Hill Climbing | 1 | 0.03 | Yes |
| Best First | 4 | 0.15 | Yes |
| A* | 4 | 0.10 | Yes |

### Harder Formula (5 variables, 8 clauses):
| Algorithm | Nodes Explored | Time (ms) | Satisfiable |
|-----------|----------------|-----------|-------------|
| BFS | 31 | 0.188 | Yes |
| DFS | 7 | 0.033 | Yes |
| IDFS | 61 | 0.155 | Yes |
| Hill Climbing | 2 | 0.063 | Yes |
| Best First | 6 | 0.143 | Yes |
| A* | 6 | 0.298 | Yes |

## Algorithm Selection Guidelines

### Choose BFS when:
- Solution depth is shallow
- Memory is not a constraint
- You need optimal solution

### Choose DFS when:
- Memory is limited
- Solution is deep
- You need any solution quickly

### Choose IDFS when:
- You want BFS optimality with DFS memory usage
- Unknown solution depth
- Balanced approach needed

### Choose Hill Climbing when:
- Local search is acceptable
- Quick approximate solutions needed
- Memory is extremely limited

### Choose Best First when:
- Good heuristic available
- Want to exploit problem structure
- Don't need optimality guarantee

### Choose A* when:
- Optimal solution required
- Admissible heuristic available
- Can afford memory cost

## Implementation Tips

### Data Structure Design:
- Use bit vectors for large formulas
- Implement efficient clause watching
- Cache heuristic evaluations

### Optimization Techniques:
- Unit propagation preprocessing
- Pure literal elimination
- Clause learning (for DPLL-based approaches)
- Random restarts for local search

### Heuristic Design:
- Combine multiple heuristic components
- Normalize heuristic values
- Adapt heuristics based on problem phase

## Conclusion

The choice of algorithm and heuristic depends on:
- Problem size and complexity
- Available computational resources
- Required solution quality
- Time constraints

For most practical 3-SAT instances, A* with a good heuristic or DPLL-based approaches with modern heuristics provide the best balance of performance and completeness.