"""
Agent Registry for QualiLens.

This module manages the registration and discovery of available agents
that the orchestrator can use to process user queries.
"""

import logging
from typing import Dict, List, Optional, Type
from .agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing available agents.
    
    This class handles agent registration, discovery, and provides
    metadata for agent selection.
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent (BaseAgent): The agent to register
        """
        agent_name = agent.name
        if agent_name in self._agents:
            logger.warning(f"Agent '{agent_name}' is already registered. Overwriting.")
        
        self._agents[agent_name] = agent
        logger.info(f"Registered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name (str): Name of the agent to retrieve
            
        Returns:
            Optional[BaseAgent]: The agent if found, None otherwise
        """
        return self._agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            Dict[str, BaseAgent]: Dictionary of all registered agents
        """
        return self._agents.copy()
    
    def get_agent_names(self) -> List[str]:
        """
        Get list of all registered agent names.
        
        Returns:
            List[str]: List of agent names
        """
        return list(self._agents.keys())
    
    def get_agent_by_capability(self, capability: str) -> List[BaseAgent]:
        """
        Get agents that have a specific capability.
        
        Args:
            capability (str): The capability to search for
            
        Returns:
            List[BaseAgent]: List of agents with the capability
        """
        matching_agents = []
        for agent in self._agents.values():
            if capability in agent.capabilities:
                matching_agents.append(agent)
        return matching_agents
    
    def get_available_agents_description(self) -> str:
        """
        Get a formatted description of all available agents for LLM consumption.
        
        Returns:
            str: Formatted description of all agents
        """
        descriptions = []
        for name, agent in self._agents.items():
            desc = f"Agent: {name}\n"
            desc += f"Description: {agent.description}\n"
            desc += f"Capabilities: {', '.join(agent.capabilities)}\n"
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_name (str): Name of the agent to unregister
            
        Returns:
            bool: True if agent was unregistered, False if not found
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        return False
    
    def clear_registry(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        logger.info("Cleared all agents from registry")
    
    def is_agent_registered(self, agent_name: str) -> bool:
        """
        Check if an agent is registered.
        
        Args:
            agent_name (str): Name of the agent to check
            
        Returns:
            bool: True if agent is registered, False otherwise
        """
        return agent_name in self._agents
