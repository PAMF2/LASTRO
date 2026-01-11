"""
Ferramentas base para os agentes
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """Classe base para todas as ferramentas"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "Sem descrição"
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Executa a ferramenta"""
        pass
    
    def to_agno_tool(self):
        """Converte para formato do Agno"""
        # Implementação específica para o framework Agno
        pass
