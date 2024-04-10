import itertools
import math
from typing import List

from data_schema import Instance, Item, Solution
from ortools.sat.python.cp_model import FEASIBLE, OPTIMAL, CpModel, CpSolver


class MultiKnapsackSolver:
    """
    This class can be used to solve the Multi-Knapsack problem
    (also the standard knapsack problem, if only one capacity is used).

    Attributes:
    - instance (Instance): The multi-knapsack instance
        - items (List[Item]): a list of Item objects representing the items to be packed.
        - capacities (List[int]): a list of integers representing the capacities of the knapsacks.
    - model (CpModel): a CpModel object representing the constraint programming model.
    - solver (CpSolver): a CpSolver object representing the constraint programming solver.
    """

    def __init__(self, instance: Instance):
        """
        Initialize the solver with the given Multi-Knapsack instance.

        Args:
        - instance (Instance): an Instance object representing the Multi-Knapsack instance.
        """
        self.items = instance.items
        self.capacities = instance.capacities
        self.model = CpModel()
        self.solver = CpSolver()
        self.solver.parameters.log_search_progress = True
        self.x = []
        for i in range(len(self.items)):
            temp = []
            for j in range(len(self.capacities)):
                temp.append(self.model.NewBoolVar(f"x_{i}_{j}"))
            self.x.append(temp)
        
        for j in range(len(self.capacities)):            
            self.model.Add(sum(self.x[i][j] * self.items[i].weight for i in range(len(self.items))) <= self.capacities[j])
        for i in range(len(self.items)):
            self.model.Add(sum(self.x[i][j] for j in range(len(self.capacities))) <= 1)
        self.model.Maximize(sum(sum(self.x[i][j] for j in range(len(self.capacities))) * self.items[i].value for i in range(len(self.items))))
        # TODO: Implement me!



    def solve(self, timelimit: float = math.inf) -> Solution:
        """
        Solve the Multi-Knapsack instance with the given time limit.

        Args:
        - timelimit (float): time limit in seconds for the cp-sat solver.

        Returns:
        - Solution: a list of lists of Item objects representing the items packed in each knapsack
        """
        status = self.solver.Solve(self.model)
        assert status == OPTIMAL
        
        knapsacks = []
        for j in range(len(self.capacities)):
            sacks = []
            for i in range(len(self.items)):
                if(self.solver.value(self.x[i][j]) == 1):
                    sacks.append(self.items[i])
            
            knapsacks.append(sacks)
        # handle given time limit
        if timelimit <= 0.0:
            return Solution(knapsacks=[])  # empty solution
        elif timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
        # TODO: Implement me!
        return Solution(knapsacks= knapsacks)  # empty solution
