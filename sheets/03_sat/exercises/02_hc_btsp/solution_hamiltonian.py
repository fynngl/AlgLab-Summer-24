import itertools
from typing import List, Optional, Tuple

import networkx as nx
from pysat.solvers import Solver as SATSolver


class HamiltonianCycleModel:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self.solver = SATSolver("Minicard")
        self.assumptions = []
        self.vars = {(u,v): i+1 for i, (u,v) in enumerate(graph.edges)}
        self.vars.update({(v,u): i+1 for i, (u,v) in enumerate(graph.edges)})
        self.reverse = {i: (u,v) for (u,v), i in self.vars.items()}
        self.x = [self.vars[v] for v in self.graph.edges]


    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """
        Solves the Hamiltonian Cycle Problem. If a HC is found,
        its edges are returned as a list.
        If the graph has no HC, 'None' is returned.
        """
        self.solver.add_atmost(self.x, len(self.graph.nodes))
        for v in self.graph.nodes:
            connections = [self.vars[(u,v)] for u,v,weight in self.graph.edges(v, data=True)]
            self.solver.add_clause(connections)
            self.solver.add_atmost(connections, 2)
            not_connections = [-var for var in connections]
            self.solver.add_atmost(not_connections, len(connections) - 2)
   
        while True:
            solution = None
            if self.solver.solve():
                solution = self.solver.get_model()
            else:
                return solution
            
            selected = [self.reverse[i] for i in solution if i > 0]
            components = list(nx.connected_components(self.graph.edge_subgraph(selected)))
            if len(components) > 1:
                for comp in components:
                    edges = []
                    for v in comp:
                        for u in self.graph.nodes:
                            if u not in comp:
                               if (u,v) in self.vars:
                                    edges.append(self.vars[(u,v)])
                    self.solver.add_clause(edges)
            else:
                return selected
                
