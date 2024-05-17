"""
Implement the Dantzig-Fulkerson-Johnson formulation for the TSP.
"""#ramwe7-Nikjyg-fizrum

import typing

import gurobipy as gp
from gurobipy import GRB
import networkx as nx




class GurobiTspRelaxationSolver:
    """
    IMPLEMENT ME!
    """

    def __init__(self, G: nx.Graph):
        """
        G is a weighted networkx graph, where the weight of an edge is stored in the
        "weight" attribute. It is strictly positive.
        """
        self.graph = G
        assert (
            G.number_of_edges() == G.number_of_nodes() * (G.number_of_nodes() - 1) / 2
        ), "Invalid graph"
        assert all(
            weight > 0 for _, _, weight in G.edges.data("weight", default=None)
        ), "Invalid graph"
        self.model = gp.Model()
        self.sorted_edges = list(self.graph.edges)
        self.x = [self.model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{u},{v}", ub=1, lb=0) for u,v in self.sorted_edges]
        self.model.update()
        self.vars = {self.sorted_edges[i]: self.x[i] for i in range(len(self.x))}
        self.vars.update({(v,u): var for (u,v), var in self.vars.items()})
        for v in self.graph.nodes:
            connections = [self.vars[e] for e in self.graph.edges if v in e]
            self.model.addConstr(sum(connections) == 2)
        self.model.setObjective(gp.quicksum(weight * self.vars[u,v] for (u,v,weight) in self.graph.edges(data="weight")), GRB.MINIMIZE)


    def get_lower_bound(self) -> float:
        """
        Return the current lower bound.
        """
        return self.model.ObjBound

    def get_solution(self) -> typing.Optional[nx.Graph]:
        """
        Return the current solution as a graph.
        """
        if self.model.status == GRB.OPTIMAL:
            selected = [(u,v) for (u,v) in self.graph.edges if self.vars[(u,v)].X > 0.01]
            return self.graph.edge_subgraph(selected)

    def get_objective(self) -> typing.Optional[float]:
        """
        Return the objective value of the last solution.
        """
        return round(self.model.ObjVal)

    def solve(self) -> None:
        """
        Solve the model and return the objective value and the lower bound.
        """
        # Set parameters for the solver.
        self.model.Params.LogToConsole = 1
        while True:
            self.model.optimize()
            selected = [(u,v) for (u,v) in self.graph.edges if self.vars[(u,v)].X >= 0.01]
            solution = self.graph.edge_subgraph(selected)
            comps = list(nx.connected_components(solution))
            if len(comps) > 1:
                for c in comps:
                        edges = [e for e in self.graph.edges if (e[0] in c) ^ (e[1] in c)]
                        if len(edges) > 0:
                            #print(f"sum: {sum(self.vars[edge].X for edge in edges)}")
                            self.model.addConstr(sum(self.vars[edge] for edge in edges) >= 2)
            else:
                if self.model.status == GRB.OPTIMAL:
                    #selected = [(u,v) for (u,v) in self.graph.edges if self.vars[(u,v)].X >= 0.01]
                    solution = nx.Graph()
                    x_vars = {edge: self.vars[edge].X for edge in self.graph.edges}
                    nx.set_edge_attributes(solution, x_vars, "x")
                return solution
