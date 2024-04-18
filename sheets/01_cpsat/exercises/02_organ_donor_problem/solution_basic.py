import math

import networkx as nx
from data_schema import Donation, Solution
from database import TransplantDatabase
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class CrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param Database database: The organ donor/recipients database.
        """
        self.database = database
        donors = self.database.get_all_donors()
        recipients = self.database.get_all_recipients()

        self.model = CpModel()
        self.x = []
        for i in range(len(recipients)):
            temp = []
            for j in range(len(donors)):
                temp.append(self.model.NewBoolVar(f"x_{i}_{j}"))
            self.x.append(temp)
        print(1)
        for i in range(len(recipients)):
            partner_donors = self.database.get_partner_donors(recipient=recipients[i])
            self.model.Add(sum(self.x[i][j] for j in range(len(donors))) <= 1)
            self.model.Add(sum(self.x[i][j] for j in range(len(donors)) if donors[j] in partner_donors) <= 1)
            #print(1.5)
            ingoing_donations = sum(self.x[i][j] for j in range(len(donors)))
            outgoing_donations = sum(self.x[k][j] for k in range(len(recipients)) for j in range(len(donors)) if donors[j] in partner_donors)
            self.model.Add(ingoing_donations == outgoing_donations)
        print(2)
        for j in range(len(donors)):
            compatible_donors = self.database.get_compatible_recipients(donors[j])
            self.model.Add(sum(self.x[i][j] for i in range(len(recipients))) <= 1)
            self.model.Add(sum(self.x[i][j] for i in range(len(recipients)) if recipients[i] not in compatible_donors) == 0)
        print(3)
        self.model.Maximize(sum(self.x[i][j] for i in range(len(recipients)) for j in range(len(donors))))

        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True


    def optimize(self, timelimit: float = math.inf) -> Solution:
        """
        Solves the constraint programming model and returns the optimal solution (if found within time limit).
        :param timelimit: The maximum time limit for the solver.
        :return: A list of Donation objects representing the best solution, or None if no solution was found.
        """
        status = self.solver.Solve(self.model)
        assert status == OPTIMAL
        
        donations = []
        for j in range(len(self.database.get_all_donors())):
            for i in range(len(self.database.get_all_recipients())):
                if self.solver.Value(self.x[i][j]) == 1:
                    donations.append(Donation(donor=self.database.get_all_donors()[j], recipient=self.database.get_all_recipients()[i]))
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
        return Solution(donations=donations)
