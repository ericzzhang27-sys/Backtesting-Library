from abc import ABC, abstractmethod
from btlib.core.order_types import Fill


class CostModel(ABC):
    @abstractmethod
    def compute(self, fill: Fill)-> tuple[float, float]:
        """
        Docstring for compute
        
        :param self: Description
        :param fill: Takes a fill object
        :type fill: Fill
        :return: A tuple of fees, slippage
        :rtype: tuple[float, float]
        """
        raise NotImplementedError