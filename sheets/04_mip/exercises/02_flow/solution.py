import gurobipy as gb
import networkx as nx
from data_schema import Instance, Solution
from gurobipy import GRB



class MiningRoutingSolver:
    def __init__(self, instance: Instance) -> None:
        self.map = instance.map
        self.tunnels = self.map.tunnels
        self.mines = self.map.mines
        #self.map.mines.sort()
        self.budget = instance.budget
        self.model = gb.Model()
        #self.x = [self.model.addVar(vtype=GRB.BINARY, name=f"x_{t.location_a}_{t.location_b}") for t in self.map.tunnels]
        #self.direct_vars = [self.model.addVar(vtype=GRB.BINARY, name=f"t_{t.location_a}_{t.location_b}") for t in self.map.tunnels]
        #self.vars = {self.map.tunnels[i]: self.x[i] for i in range(len(self.x))}
        #self.directions = {self.map.tunnels[i]: self.direct_vars[i] for i in range(len(self.map.tunnels))}
        #self.flow_dict = {}

        #self.model.addConstr(sum(self.map.tunnels[i].reinforcement_costs * self.x[i] for i in range(len(self.x))) <= instance.budget)
        #self.model.setObjective(gb.quicksum(self.x[i] * self.map.tunnels[i].used_throughput for i in range(len(self.map.tunnels)) if self.map.elevator.id == self.map.tunnels[i].location_a or self.map.elevator.id == self.map.tunnels[i].location_b), GRB.MAXIMIZE)
        self.graph = nx.Graph()
        for v in self.mines:
            self.graph.add_node(v.id, production=v.ore_per_hour)    
        for e in self.tunnels:
            self.graph.add_edge(e.location_a, e.location_b, cost=e.reinforcement_costs, ore_cap=e.throughput_per_hour)
        
        edge_list = list(self.graph.edges)   
        self.x = [self.model.addVar(vtype=GRB.BINARY, name=f"x_{u}_{v}") for (u,v) in self.graph.edges]
        self.y = [self.model.addVar(vtype=GRB.BINARY, name=f"y_{u}_{v}") for (u,v) in self.graph.edges]
        self.max_flow = 0

        self.directions = {edge_list[i]: self.y[i] for i in range(len(self.y))}
        self.vars = {edge_list[i]: self.x[i] for i in range(len(self.y))} 
        
        self.model.addConstr(gb.quicksum(self.x[i] * self.graph[edge_list[i][0]][edge_list[i][1]]["cost"] for i in range(len(self.graph.edges))) <= instance.budget)
        self.model.setObjective(self.max_flow, GRB.MAXIMIZE)
            
        



    def solve(self) -> Solution:
        """
        Calculate the optimal solution to the problem.
        Returns the "flow" as a list of tuples, each tuple with two entries:
            - The *directed* edge tuple. Both entries in the edge should be ints, representing the ids of locations.
            - The throughput/utilization of the edge, in goods per hour
        """
        self.model.Params.LogToConsole = 1
        self.model.Params.lazyConstraints = 1
        
        flow_dict = {}
        solution_edges = []
        output = []
        
        def callback(model, where):
            #output = []
            #if where == gb.GRB.Callback.MIPSOL:
                # add selected edges to subgraph if they are chosen and order their nodes according to the direction chosen in direct_vars
                #selected = [(self.map.tunnels[i].location_a, self.map.tunnels[i].location_b, self.map.tunnels[i].throughput_per_hour) for i in self.map.tunnels if (self.model.cbGetSolution(self.vars[self.map.tunnels[i]]) > 0.5) and (self.model.cbGetSolution(self.directions[self.map.tunnels[i]]) > 0.5)]
                #selected.append([[(self.map.tunnels[i].location_b, self.map.tunnels[i].location_a, self.map.tunnels[i].throughput_per_hour) for i in self.map.tunnels if (self.model.cbGetSolution(self.vars[self.map.tunnels[i]]) > 0.5) and (self.model.cbGetSolution(self.directions[self.map.tunnels[i]]) <= 0.5)]])
                #solution = nx.DiGraph()
                #solution.add_edges_from(selected)
                #for v in solution.nodes:   
                    #flow_value, self.flow_dict = nx.maximum_flow(solution, v, self.map.elevator.id)
                    #for u in solution.nodes():
                        #if u != v and u != self.map.elevator.id:
                            #inflow = sum(self.flow_dict[prev][u] for prev in solution.predecessors(u))
                            #outflow = sum(self.flow_dict[u][next] for next in solution.successors(u))
                            #self.model.addConstr(self.map.mines[u] + inflow == outflow) 
                    
            
            if where == gb.GRB.Callback.MIPSOL:
                solution = nx.DiGraph()
                for v,prod in self.graph.nodes(data=True):
                    if v != self.map.elevator.id:
                        b = prod["production"]
                        solution.add_node(v, production=b)
                    else:
                        solution.add_node(v, production=0)
                for edge in self.graph.edges:
                    # if edge is chosen
                    if self.model.cbGetSolution(self.vars[edge]) > 0.5: 
                        # if the default direction is chosen
                        if self.model.cbGetSolution(self.directions[self.vars[edge]]) > 0.5:
                            solution.add_edge(edge[1], edge[0], cost=self.graph[edge[0]][edge[1]]["cost"], ore_cap=self.graph[edge[0]][edge[1]]["ore_cap"])
                        else:
                            solution.add_edge(edge[0], edge[1], cost=self.graph[edge[0]][edge[1]]["cost"], ore_cap=self.graph[edge[0]][edge[1]]["ore_cap"])
                solution_edges = solution.edges
                            
                for v in solution.nodes:   
                    self.max_flow, flow_dict = nx.maximum_flow(solution, v, self.map.elevator.id)
                    for u,prod in solution.nodes(data=True):
                        if u != v and u != self.map.elevator.id:
                            inflow = sum(flow_dict[prev][u] for prev in solution.predecessors(u))
                            outflow = sum(flow_dict[u][next] for next in solution.successors(u))
                            #print(prod["production"] + inflow)
                            #print(outflow)
                            self.model.addConstr(prod["production"] + inflow == outflow) 
                
                
        self.model.optimize(callback)
            
        if self.model.status == GRB.OPTIMAL:
            for v in self.graph.nodes:
                for u in self.graph.nodes:
                    if (u,v) in solution_edges:
                        output.append(((v, u), flow_dict[v][u]))
            print(output)
            return output