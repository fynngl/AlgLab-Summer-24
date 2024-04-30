import math
from typing import Dict, Iterable, List

import networkx as nx
from pysat.solvers import Solver as SATSolver



class KCentersSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the k-centers problem on the given networkx graph.
        The graph is not necessarily complete, so not all nodes are neighbors.
        The distance between two neighboring nodes is a numeric value (int / float), saved as
        an edge data parameter called "weight".
        There are multiple ways to access this data, and networkx also implements
        several algorithms that automatically make use of this value.
        Check the networkx documentation for more information!
        """
        self.graph = graph
        self.distances = {}
        self.vars = {node: i+1 for i, node in enumerate(graph.nodes)}
        self.reverse = {i: node for node, i in self.vars.items()}
        self.x = [self.vars[v] for v in self.graph.nodes]
        for v in self.graph.nodes():
            for w in self.graph.nodes():
                    self.distances[(v,w)] = nx.dijkstra_path_length(self.graph, v, w)
        #print(f"dis: {self.distances}")
                    

    def solve_heur(self, k: int, m: int) -> List[int]:
        """
        Calculate a heuristic solution to the k-centers problem.
        Returns the k selected centers as a list of ints.
        (nodes will be ints in the given graph).
        """
        centers = []
        sat = SATSolver("MiniCard")
        sat.add_atmost(self.x, k)
        for v in self.graph.nodes:
            in_range = [w for w in self.graph.nodes if self.distances[(v,w)] <= m]
            #print(f"inrange: {in_range}")
            sat.add_clause(in_range)
        #print(f"solve: {sat.solve()}")            
        if sat.solve():
            centers = sat.get_model()
        return centers


    def solve(self, k: int) -> List[int]:
        """
        For the given parameter k, calculate the optimal solution
        to the k-centers solution and return the selected centers as a list.
        """
        previous_solution = []
        count = 0
        m = max(self.distances.values())
        prev_m = m
        centers = self.solve_heur(k, m)
        while len(centers) > 0:
            #print(len(centers))
            m = 0
            selected = [self.reverse[self.x[i]] for i in range(len(centers)) if centers[i] > 0]
            for c in selected:
                for v in self.graph.nodes:
                    if c != v:
                        if m < self.distances[(c, v)] and self.distances[(c, v)] < prev_m:
                            m = self.distances[(c, v)]
            print(f"m,pn: {m, prev_m, m==prev_m}")
            prev_m = m
            previous_solution = centers
            centers = self.solve_heur(k, m)
            count += 1
        print(f"prev: {previous_solution}")
        print(f"count: {count}")
        solution = [i for i in previous_solution if i > 0]
        print(solution)
        #print(min(len(self.connections[e]) for e in self.connections))
        return solution