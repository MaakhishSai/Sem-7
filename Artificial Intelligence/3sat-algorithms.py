#!/usr/bin/env python3
"""
3-SAT Problem Solving Algorithms
Implementation of BFS, DFS, IDFS, Hill Climbing, Best First Search, and A* for 3-SAT

Author: AI Assistant
Date: 2025
"""

import random
import heapq
from collections import deque
import time

class Clause:
    """Represents a 3-SAT clause with three literals"""
    def __init__(self, literals):
        self.literals = literals  # List of literals (positive or negative variables)
    
    def __str__(self):
        return f"({' OR '.join(map(str, self.literals))})"
    
    def evaluate(self, assignment):
        """Evaluate clause given variable assignment"""
        for literal in self.literals:
            var = abs(literal)
            value = assignment.get(var, None)
            if value is not None:
                # If literal is positive and value is True, OR literal is negative and value is False
                if (literal > 0 and value) or (literal < 0 and not value):
                    return True
        return False
    
    def is_unit(self, assignment):
        """Check if clause is unit (has exactly one unassigned literal)"""
        unassigned = []
        satisfied = False
        
        for literal in self.literals:
            var = abs(literal)
            value = assignment.get(var, None)
            if value is None:
                unassigned.append(literal)
            else:
                if (literal > 0 and value) or (literal < 0 and not value):
                    satisfied = True
                    break
        
        return not satisfied and len(unassigned) == 1, unassigned[0] if not satisfied and len(unassigned) == 1 else None

class SATFormula:
    """Represents a 3-SAT formula"""
    def __init__(self, clauses, num_vars):
        self.clauses = clauses
        self.num_vars = num_vars
    
    def __str__(self):
        return " AND ".join(str(clause) for clause in self.clauses)
    
    def evaluate(self, assignment):
        """Evaluate entire formula"""
        return all(clause.evaluate(assignment) for clause in self.clauses)
    
    def is_satisfied(self, assignment):
        """Check if formula is satisfied by assignment"""
        return self.evaluate(assignment)
    
    def count_satisfied_clauses(self, assignment):
        """Count number of satisfied clauses"""
        return sum(1 for clause in self.clauses if clause.evaluate(assignment))

class SATState:
    """Represents a state in the search space"""
    def __init__(self, assignment, depth=0):
        self.assignment = assignment.copy()  # Variable assignments
        self.depth = depth
        self.id = id(self)  # Unique identifier for comparison
    
    def __str__(self):
        return f"Assignment: {self.assignment}, Depth: {self.depth}"
    
    def __lt__(self, other):
        """Less than comparison for priority queue"""
        return self.id < other.id
    
    def is_complete(self, num_vars):
        return len(self.assignment) == num_vars
    
    def get_next_variable(self, num_vars):
        """Get next unassigned variable"""
        for i in range(1, num_vars + 1):
            if i not in self.assignment:
                return i
        return None

def check_conflict(formula, assignment):
    """Check if current assignment leads to a conflict"""
    for clause in formula.clauses:
        all_false = True
        has_unassigned = False
        
        for literal in clause.literals:
            var = abs(literal)
            if var not in assignment:
                has_unassigned = True
                break
            else:
                value = assignment[var]
                if (literal > 0 and value) or (literal < 0 and not value):
                    all_false = False
                    break
        
        if not has_unassigned and all_false:
            return True  # Conflict found
    return False

# ============================================================================
# 1. BREADTH-FIRST SEARCH (BFS)
# ============================================================================

def sat_bfs(formula):
    """Solve 3-SAT using Breadth-First Search"""
    start_time = time.time()
    nodes_explored = 0
    
    queue = deque([SATState({})])
    
    while queue:
        current_state = queue.popleft()
        nodes_explored += 1
        
        # Check if current assignment is complete
        if current_state.is_complete(formula.num_vars):
            if formula.is_satisfied(current_state.assignment):
                return {
                    'satisfiable': True,
                    'assignment': current_state.assignment,
                    'nodes_explored': nodes_explored,
                    'time_taken': time.time() - start_time
                }
            continue
        
        # Check for early conflict
        if check_conflict(formula, current_state.assignment):
            continue
        
        # Get next variable to assign
        next_var = current_state.get_next_variable(formula.num_vars)
        if next_var is None:
            continue
        
        # Try both True and False assignments
        for value in [True, False]:
            new_assignment = current_state.assignment.copy()
            new_assignment[next_var] = value
            new_state = SATState(new_assignment, current_state.depth + 1)
            queue.append(new_state)
    
    return {
        'satisfiable': False,
        'assignment': None,
        'nodes_explored': nodes_explored,
        'time_taken': time.time() - start_time
    }

# ============================================================================
# 2. DEPTH-FIRST SEARCH (DFS)
# ============================================================================

def sat_dfs(formula):
    """Solve 3-SAT using Depth-First Search"""
    start_time = time.time()
    nodes_explored = 0
    
    def dfs_recursive(assignment):
        nonlocal nodes_explored
        nodes_explored += 1
        
        # Check if assignment is complete
        if len(assignment) == formula.num_vars:
            return formula.is_satisfied(assignment)
        
        # Check for early conflict
        if check_conflict(formula, assignment):
            return False
        
        # Get next variable
        next_var = None
        for i in range(1, formula.num_vars + 1):
            if i not in assignment:
                next_var = i
                break
        
        if next_var is None:
            return False
        
        # Try True first
        assignment[next_var] = True
        if dfs_recursive(assignment):
            return True
        
        # Try False
        assignment[next_var] = False
        if dfs_recursive(assignment):
            return True
        
        # Backtrack
        del assignment[next_var]
        return False
    
    assignment = {}
    satisfiable = dfs_recursive(assignment)
    
    return {
        'satisfiable': satisfiable,
        'assignment': assignment if satisfiable else None,
        'nodes_explored': nodes_explored,
        'time_taken': time.time() - start_time
    }

# ============================================================================
# 3. ITERATIVE DEEPENING DEPTH-FIRST SEARCH (IDFS)
# ============================================================================

def sat_idfs(formula, max_depth=None):
    """Solve 3-SAT using Iterative Deepening Depth-First Search"""
    start_time = time.time()
    total_nodes_explored = 0
    
    if max_depth is None:
        max_depth = formula.num_vars
    
    def depth_limited_dfs(assignment, depth_limit):
        nonlocal total_nodes_explored
        total_nodes_explored += 1
        
        if len(assignment) == formula.num_vars:
            return formula.is_satisfied(assignment)
        
        if len(assignment) >= depth_limit:
            return False
        
        if check_conflict(formula, assignment):
            return False
        
        next_var = None
        for i in range(1, formula.num_vars + 1):
            if i not in assignment:
                next_var = i
                break
        
        if next_var is None:
            return False
        
        # Try True first
        assignment[next_var] = True
        if depth_limited_dfs(assignment, depth_limit):
            return True
        
        # Try False
        assignment[next_var] = False
        if depth_limited_dfs(assignment, depth_limit):
            return True
        
        # Backtrack
        del assignment[next_var]
        return False
    
    # Iteratively increase depth limit
    for depth in range(1, max_depth + 1):
        assignment = {}
        if depth_limited_dfs(assignment, depth):
            return {
                'satisfiable': True,
                'assignment': assignment,
                'nodes_explored': total_nodes_explored,
                'time_taken': time.time() - start_time,
                'depth_found': depth
            }
    
    return {
        'satisfiable': False,
        'assignment': None,
        'nodes_explored': total_nodes_explored,
        'time_taken': time.time() - start_time,
        'max_depth_reached': max_depth
    }

# ============================================================================
# 4. HILL CLIMBING
# ============================================================================

def sat_hill_climbing(formula, max_iterations=1000, max_restarts=10):
    """Solve 3-SAT using Hill Climbing with random restarts"""
    start_time = time.time()
    total_iterations = 0
    best_score = 0
    best_assignment = None
    
    def random_assignment():
        """Generate random assignment"""
        return {i: random.choice([True, False]) for i in range(1, formula.num_vars + 1)}
    
    def get_neighbors(assignment):
        """Get all neighbors by flipping one variable"""
        neighbors = []
        for var in range(1, formula.num_vars + 1):
            neighbor = assignment.copy()
            neighbor[var] = not neighbor[var]
            neighbors.append(neighbor)
        return neighbors
    
    def evaluate_assignment(assignment):
        """Evaluate assignment (number of satisfied clauses)"""
        return formula.count_satisfied_clauses(assignment)
    
    for restart in range(max_restarts):
        # Start with random assignment
        current_assignment = random_assignment()
        current_score = evaluate_assignment(current_assignment)
        
        for iteration in range(max_iterations):
            total_iterations += 1
            
            # Check if we found a solution
            if current_score == len(formula.clauses):
                return {
                    'satisfiable': True,
                    'assignment': current_assignment,
                    'iterations': total_iterations,
                    'restarts': restart + 1,
                    'time_taken': time.time() - start_time,
                    'final_score': current_score
                }
            
            # Find best neighbor
            best_neighbor = None
            best_neighbor_score = current_score
            
            for neighbor in get_neighbors(current_assignment):
                neighbor_score = evaluate_assignment(neighbor)
                if neighbor_score > best_neighbor_score:
                    best_neighbor = neighbor
                    best_neighbor_score = neighbor_score
            
            # If no improvement possible, break (local optimum)
            if best_neighbor is None:
                break
            
            # Move to best neighbor
            current_assignment = best_neighbor
            current_score = best_neighbor_score
        
        # Update best solution found so far
        if current_score > best_score:
            best_score = current_score
            best_assignment = current_assignment
    
    return {
        'satisfiable': best_score == len(formula.clauses),
        'assignment': best_assignment,
        'iterations': total_iterations,
        'restarts': max_restarts,
        'time_taken': time.time() - start_time,
        'final_score': best_score
    }

# ============================================================================
# 5. HEURISTICS FOR INFORMED SEARCH
# ============================================================================

def unsatisfied_clauses_heuristic(formula, assignment):
    """Count how many unsatisfied clauses each variable appears in"""
    var_counts = {}
    
    for clause in formula.clauses:
        if not clause.evaluate(assignment):
            for literal in clause.literals:
                var = abs(literal)
                if var not in assignment:
                    var_counts[var] = var_counts.get(var, 0) + 1
    
    return var_counts

def jeroslow_wang_heuristic(formula, assignment):
    """Jeroslow-Wang heuristic: weight literals by clause length"""
    literal_weights = {}
    
    for clause in formula.clauses:
        if not clause.evaluate(assignment):
            unassigned_literals = [lit for lit in clause.literals if abs(lit) not in assignment]
            clause_weight = 2 ** (-len(unassigned_literals))
            
            for literal in unassigned_literals:
                literal_weights[literal] = literal_weights.get(literal, 0) + clause_weight
    
    # Convert to variable weights
    var_weights = {}
    for literal, weight in literal_weights.items():
        var = abs(literal)
        var_weights[var] = var_weights.get(var, 0) + weight
    
    return var_weights

def most_constraining_variable_heuristic(formula, assignment):
    """Choose variable that appears in most unsatisfied clauses"""
    var_constraint_count = {}
    
    for clause in formula.clauses:
        if not clause.evaluate(assignment):
            for literal in clause.literals:
                var = abs(literal)
                if var not in assignment:
                    var_constraint_count[var] = var_constraint_count.get(var, 0) + 1
    
    return var_constraint_count

def unit_propagation_heuristic(formula, assignment):
    """Prioritize variables in unit clauses"""
    unit_vars = {}
    
    for clause in formula.clauses:
        is_unit, literal = clause.is_unit(assignment)
        if is_unit:
            var = abs(literal)
            unit_vars[var] = unit_vars.get(var, 0) + 10  # High priority for unit clauses
    
    return unit_vars

# ============================================================================
# 6. BEST FIRST SEARCH
# ============================================================================

def sat_best_first_search(formula, heuristic_func=unsatisfied_clauses_heuristic):
    """Solve 3-SAT using Best First Search with given heuristic"""
    start_time = time.time()
    nodes_explored = 0
    
    # Priority queue: (priority, counter, state)
    priority_queue = [(0, 0, SATState({}))]
    visited = set()
    counter = 1
    
    while priority_queue:
        priority, _, current_state = heapq.heappop(priority_queue)
        nodes_explored += 1
        
        # Convert assignment to tuple for hashing
        assignment_tuple = tuple(sorted(current_state.assignment.items()))
        if assignment_tuple in visited:
            continue
        visited.add(assignment_tuple)
        
        # Check if assignment is complete
        if current_state.is_complete(formula.num_vars):
            if formula.is_satisfied(current_state.assignment):
                return {
                    'satisfiable': True,
                    'assignment': current_state.assignment,
                    'nodes_explored': nodes_explored,
                    'time_taken': time.time() - start_time
                }
            continue
        
        # Check for early conflict
        if check_conflict(formula, current_state.assignment):
            continue
        
        # Get next variable using heuristic
        heuristic_scores = heuristic_func(formula, current_state.assignment)
        if not heuristic_scores:
            next_var = current_state.get_next_variable(formula.num_vars)
        else:
            next_var = max(heuristic_scores.keys(), key=lambda x: heuristic_scores[x])
        
        if next_var is None:
            continue
        
        # Try both assignments, prioritize based on heuristic
        for value in [True, False]:
            new_assignment = current_state.assignment.copy()
            new_assignment[next_var] = value
            new_state = SATState(new_assignment, current_state.depth + 1)
            
            # Calculate priority (lower is better)
            satisfied_count = formula.count_satisfied_clauses(new_assignment)
            priority = len(formula.clauses) - satisfied_count
            
            heapq.heappush(priority_queue, (priority, counter, new_state))
            counter += 1
    
    return {
        'satisfiable': False,
        'assignment': None,
        'nodes_explored': nodes_explored,
        'time_taken': time.time() - start_time
    }

# ============================================================================
# 7. A* ALGORITHM
# ============================================================================

def sat_a_star(formula, heuristic_func=unsatisfied_clauses_heuristic):
    """Solve 3-SAT using A* search algorithm"""
    start_time = time.time()
    nodes_explored = 0
    
    def manhattan_distance_heuristic(assignment):
        """Admissible heuristic: minimum number of variable assignments needed"""
        return formula.num_vars - len(assignment)
    
    def unsatisfied_clauses_h(assignment):
        """Heuristic based on unsatisfied clauses"""
        unsatisfied = 0
        for clause in formula.clauses:
            if not clause.evaluate(assignment):
                unsatisfied += 1
        return unsatisfied
    
    def combined_heuristic(assignment):
        """Combine different heuristics"""
        unassigned_vars = manhattan_distance_heuristic(assignment)
        unsatisfied = unsatisfied_clauses_h(assignment)
        return unassigned_vars + unsatisfied
    
    # Priority queue: (f_score, g_score, counter, state)
    priority_queue = [(combined_heuristic({}), 0, 0, SATState({}))]
    visited = set()
    counter = 1
    
    while priority_queue:
        f_score, g_score, _, current_state = heapq.heappop(priority_queue)
        nodes_explored += 1
        
        # Convert assignment to tuple for hashing
        assignment_tuple = tuple(sorted(current_state.assignment.items()))
        if assignment_tuple in visited:
            continue
        visited.add(assignment_tuple)
        
        # Check if assignment is complete
        if current_state.is_complete(formula.num_vars):
            if formula.is_satisfied(current_state.assignment):
                return {
                    'satisfiable': True,
                    'assignment': current_state.assignment,
                    'nodes_explored': nodes_explored,
                    'time_taken': time.time() - start_time,
                    'path_cost': g_score
                }
            continue
        
        # Check for early conflict
        if check_conflict(formula, current_state.assignment):
            continue
        
        # Get next variable using heuristic
        heuristic_scores = heuristic_func(formula, current_state.assignment)
        if not heuristic_scores:
            next_var = current_state.get_next_variable(formula.num_vars)
        else:
            next_var = max(heuristic_scores.keys(), key=lambda x: heuristic_scores[x])
        
        if next_var is None:
            continue
        
        # Try both assignments
        for value in [True, False]:
            new_assignment = current_state.assignment.copy()
            new_assignment[next_var] = value
            new_state = SATState(new_assignment, current_state.depth + 1)
            
            # Calculate costs
            new_g_score = g_score + 1  # Cost of making one more assignment
            h_score = combined_heuristic(new_assignment)
            new_f_score = new_g_score + h_score
            
            heapq.heappush(priority_queue, (new_f_score, new_g_score, counter, new_state))
            counter += 1
    
    return {
        'satisfiable': False,
        'assignment': None,
        'nodes_explored': nodes_explored,
        'time_taken': time.time() - start_time
    }

# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

def create_example_formula():
    """Create example 3-SAT formula"""
    clauses = [
        Clause([1, 2, 3]),      # x1 OR x2 OR x3
        Clause([-1, 2, 3]),     # NOT x1 OR x2 OR x3
        Clause([-1, -2, -3]),   # NOT x1 OR NOT x2 OR NOT x3
        Clause([1, -2, 3])      # x1 OR NOT x2 OR x3
    ]
    return SATFormula(clauses, 3)

def create_harder_formula():
    """Create a more challenging 3-SAT instance"""
    clauses = [
        Clause([1, 2, 3]),        # x1 OR x2 OR x3
        Clause([-1, 2, -4]),      # NOT x1 OR x2 OR NOT x4
        Clause([-2, 3, 4]),       # NOT x2 OR x3 OR x4
        Clause([1, -3, -4]),      # x1 OR NOT x3 OR NOT x4
        Clause([-1, -2, 4]),      # NOT x1 OR NOT x2 OR x4
        Clause([2, -3, -5]),      # x2 OR NOT x3 OR NOT x5
        Clause([1, 4, 5]),        # x1 OR x4 OR x5
        Clause([-1, -4, -5])      # NOT x1 OR NOT x4 OR NOT x5
    ]
    return SATFormula(clauses, 5)

def test_all_algorithms(formula, description=""):
    """Test all algorithms on given formula"""
    print(f"\n{'='*50}")
    print(f"Testing {description}")
    print(f"Formula: {formula}")
    print(f"{'='*50}")
    
    algorithms = [
        ("BFS", sat_bfs),
        ("DFS", sat_dfs),
        ("IDFS", sat_idfs),
        ("Hill Climbing", sat_hill_climbing),
        ("Best First (Unsat Clauses)", lambda f: sat_best_first_search(f, unsatisfied_clauses_heuristic)),
        ("Best First (JW)", lambda f: sat_best_first_search(f, jeroslow_wang_heuristic)),
        ("A* (Combined)", lambda f: sat_a_star(f, unsatisfied_clauses_heuristic))
    ]
    
    results = []
    for name, algorithm in algorithms:
        print(f"\nRunning {name}...")
        if name == "Hill Climbing":
            random.seed(42)  # For reproducible results
        result = algorithm(formula)
        results.append((name, result))
        print(f"  Result: Satisfiable={result['satisfiable']}, "
              f"Nodes/Iter={result.get('nodes_explored', result.get('iterations', 'N/A'))}, "
              f"Time={result['time_taken']*1000:.3f}ms")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY - {description}")
    print(f"{'Algorithm':<25} {'Satisfiable':<12} {'Nodes/Iter':<12} {'Time (ms)':<12}")
    print("-" * 70)
    
    for name, result in results:
        satisfiable = result['satisfiable']
        nodes = result.get('nodes_explored', result.get('iterations', 'N/A'))
        time_ms = f"{result['time_taken']*1000:.3f}"
        print(f"{name:<25} {satisfiable:<12} {nodes:<12} {time_ms:<12}")

if __name__ == "__main__":
    # Test on simple example
    simple_formula = create_example_formula()
    test_all_algorithms(simple_formula, "Simple 3-SAT Formula")
    
    # Test on harder example
    harder_formula = create_harder_formula()
    test_all_algorithms(harder_formula, "Harder 3-SAT Formula")
    
    print(f"\n{'='*70}")
    print("HEURISTICS EXPLANATION:")
    print("1. Unsatisfied Clauses: Counts variables appearing in unsatisfied clauses")
    print("2. Jeroslow-Wang: Weights variables by 2^(-clause_length)")
    print("3. Most Constraining: Variable appearing in most unsatisfied clauses")
    print("4. Unit Propagation: High priority for variables in unit clauses")
    print("5. Combined A*: Manhattan distance + unsatisfied clauses count")
    print(f"{'='*70}")