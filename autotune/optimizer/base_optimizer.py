# optimizer/base_optimizer.py
from abc import ABC, abstractmethod

class BaseOptimizer(ABC):
    """Classe base para qualquer otimizador (permite futuras extensões)."""

    def __init__(self, objective_function, x0, max_iter=100, tol=1e-5):
        self.objective_function = objective_function
        self.x0 = x0
        self.max_iter = max_iter
        self.tol = tol

    @abstractmethod
    def optimize(self):
        pass