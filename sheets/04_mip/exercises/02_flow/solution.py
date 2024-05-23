import gurobipy as gb
import networkx as nx
from data_schema import Instance, Solution
from gurobipy import GRB



class MiningRoutingSolver:
    def __init__(self, instance: Instance) -> None:
        self.map = instance.map
        self.tunnels = self.map.tunnels
        self.mines = self.map.mines
        self.budget = instance.budget
        self.model = gb.Model()
        self.graph = nx.DiGraph()
        for v in self.mines:
            self.graph.add_node(v.id, production=v.ore_per_hour)    
        for e in self.tunnels:
            self.graph.add_edge(e.location_a, e.location_b, cost=e.reinforcement_costs, capacity=e.throughput_per_hour)
            self.graph.add_edge(e.location_b, e.location_a, cost=e.reinforcement_costs, capacity=e.throughput_per_hour)
        
        edge_list = list(self.graph.edges)   
        self.x = [self.model.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}") for (u,v) in self.graph.edges]
        self.y = [self.model.addVar(vtype=GRB.INTEGER, name=f"x_{u}_{v}", lb=0, ub=self.graph[u][v]["capacity"]) for (u,v) in self.graph.edges]

        self.vars = {edge_list[i]: self.x[i] for i in range(len(self.x))}
        self.usage = {edge_list[i]: self.y[i] for i in range(len(self.y))} 
        
        for u,v in self.graph.edges:
            direct_1 = self.vars[(u,v)]
            direct_2 = self.vars[(v,u)]
            self.model.addConstr(direct_1 + direct_2 <= 1)
            self.model.addConstr(self.usage[(u,v)] - self.vars[(u,v)] < self.usage[(u,v)])
        self.model.addConstr(gb.quicksum(self.x[i] * self.graph[edge_list[i][0]][edge_list[i][1]]["cost"] for i in range(len(self.graph.edges))) <= instance.budget)
        self.model.setObjective(sum(self.usage[(u,v)] for (u,v) in self.graph.edges if v == self.map.elevator.id), GRB.MAXIMIZE)
            
        



    def solve(self) -> Solution:
        """
        Calculate the optimal solution to the problem.
        Returns the "flow" as a list of tuples, each tuple with two entries:
            - The *directed* edge tuple. Both entries in the edge should be ints, representing the ids of locations.
            - The throughput/utilization of the edge, in goods per hour
        """
        self.model.Params.LogToConsole = 1
        self.model.Params.lazyConstraints = 1
        
        output = []
        
        for v,data in self.graph.nodes(data=True):
            if v != self.map.elevator.id:   
                #self.max_flow, flow_dict = nx.maximum_flow(self.graph, v, self.map.elevator.id)
                #for u,prod in self.graph.nodes(data=True):
                    #if u != v and u != self.map.elevator.id:
                        #inflow = sum(flow_dict[prev][u] for prev in self.graph.predecessors(u))
                        #outflow = sum(flow_dict[u][next] for next in self.graph.successors(u))
                        #self.model.addConstr(prod["production"] + inflow == outflow)
                inflow = sum(self.usage[(v,u)] for u in self.graph.nodes if u!=v and (v,u) in self.graph.edges and u != self.map.elevator.id)
                outflow = sum(self.usage[(u,v)] for u in self.graph.nodes if u!=v and (u,v) in self.graph.edges)
                prod = data["production"]
                self.model.addConstr(inflow + prod == outflow) 
                
                
        self.model.optimize()
            
        if self.model.status == GRB.OPTIMAL:
            for v in self.graph.nodes:
                for u in self.graph.nodes:
                    if (u,v) in self.graph.edges:
                        output.append(((v, u), self.usage[(u,v)]))
            print(output)
            return output