"""
Implement the Dantzig-Fulkerson-Johnson formulation for the TSP.
"""#ramwe7-Nikjyg-fizrum

import typing

import gurobipy as gp
from gurobipy import GRB
import networkx as nx




class GurobiTspSolver:
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
        self.x = [self.model.addVar(vtype=GRB.BINARY, name=f"x_{u},{v}") for u,v in self.sorted_edges]
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
            selected = [(u,v) for (u,v) in self.graph.edges if self.vars[(u,v)].X > 0.5]
            return self.graph.edge_subgraph(selected)

    def get_objective(self) -> typing.Optional[float]:
        """
        Return the objective value of the last solution.
        """
        return round(self.model.ObjVal)

    def solve(self, time_limit: float, opt_tol: float = 0.001) -> None:
        """
        Solve the model and return the objective value and the lower bound.
        """
        # Set parameters for the solver.
        self.model.Params.LogToConsole = 1
        self.model.Params.TimeLimit = time_limit
        self.model.Params.lazyConstraints = 1
        self.model.Params.MIPGap = (
            opt_tol  # https://www.gurobi.com/documentation/11.0/refman/mipgap.html
        )
        def callback(model, where):
            if where == gp.GRB.Callback.MIPSOL:
                selected = [(u,v) for (u,v) in self.graph.edges if self.model.cbGetSolution(self.vars[(u,v)]) > 0.5]
                solution = self.graph.edge_subgraph(selected)
                #solution = self.x.as_graph(in_callback=True)
                comps = list(nx.connected_components(solution))
                if len(comps) > 1:
                    for c in comps:
                        edges = [e for e in self.graph.edges if (e[0] in c) ^ (e[1] in c)]
                        self.model.cbLazy(sum(self.vars[edge] for edge in edges) >= 2)
        self.model.optimize(callback)
        if self.model.status == GRB.OPTIMAL:
            selected = [(u,v) for (u,v) in self.graph.edges if self.vars[(u,v)].X > 0.5]
            return self.graph.edge_subgraph(selected)
        else:
            return []
            

