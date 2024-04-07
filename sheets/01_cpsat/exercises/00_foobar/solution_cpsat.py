from data_schema import Instance, Solution
from ortools.sat.python import cp_model


def solve(instance: Instance) -> Solution:
    """
    Implement your solver for the problem here!
    """
    numbers = instance.numbers
    model = cp_model.CpModel()
    x = model.NewIntVar(min(numbers),max(numbers), "x")
    y = model.NewIntVar(min(numbers),max(numbers), "y")
    abs_diff = model.NewIntVar(0,max(numbers)-min(numbers), "abs_diff")
    #model.add(abs_diff == max(x,y)-min(x,y))
    model.AddAbsEquality(abs_diff, x - y)
    model.Maximize(abs_diff)
    
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    #print(status)
    return Solution(
        number_a=solver.value(x),
        number_b=solver.value(y),
        distance=abs(solver.value(x)-solver.value(y)),
    )
