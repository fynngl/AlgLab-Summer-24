import math
from collections import defaultdict

import networkx as nx
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class CycleLimitingCrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param Database database: The organ donor/recipients database.
        """

        self.database = database
        self.donors = self.database.get_all_donors()
        self.recipients = self.database.get_all_recipients()
        
        self.model = CpModel()
        G = nx.DiGraph()
        for i in self.recipients:
            for k in self.recipients:
                if i == k:
                    continue
                pdonors = set(self.database.get_partner_donors(i))
                cdonors = set(self.database.get_compatible_donors(k))
                if len(pdonors.intersection(cdonors)) > 0:
                    G.add_edge(i, k)
                    
        self.cycles = [cycle for cycle in nx.simple_cycles(G, 3)]
        self.y = [self.model.NewBoolVar(f"y_{cycle}") for cycle in self.cycles]
        for v in G.nodes():
            self.model.Add(sum(yi for yi, c in zip(self.y, self.cycles) if v in c) <= 1)
        self.model.Maximize(sum(yi*len(cycle) for yi,cycle in zip(self.y, self.cycles)))
        
        self.solver = CpSolver()


    def optimize(self, timelimit: float = math.inf) -> Solution:
        status = self.solver.Solve(self.model)
        assert status == OPTIMAL
        
        donations = []
        for yi, cycle in zip(self.y, self.cycles):
            if self.solver.Value(yi) == 1:
                for n in range(len(cycle)):
                    if n == len(cycle)-1:
                        donations.append(Donation(donor=list(set(self.database.get_partner_donors(cycle[len(cycle)-1])).intersection(set(self.database.get_compatible_donors(cycle[0]))))[0] , recipient=cycle[0]))
                    else:
                        donations.append(Donation(donor=list(set(self.database.get_partner_donors(cycle[n])).intersection(set(self.database.get_compatible_donors(cycle[n+1]))))[0] , recipient=cycle[n+1]))

                
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
        return Solution(donations=donations)