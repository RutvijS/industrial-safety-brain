"""
base_agent.py -- Abstract base class for all agents.

Every agent implements this interface:
  - initialize()   → prepare the agent
  - execute(ctx)    → run the agent logic
  - validate()      → check prerequisites
  - format_output() → structure the result

Agents are orchestration wrappers only.
They reuse existing services and NEVER duplicate business logic.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger("safety_brain.agents")


class BaseAgent(ABC):
    """Abstract base class for all industrial safety agents.

    Subclasses must implement execute().
    Other methods have sensible defaults.
    """

    # Subclasses set these
    name: str = "base"
    display_name: str = "Base Agent"
    icon: str = "🤖"

    def __init__(self) -> None:
        self._result: Dict[str, Any] = {}
        self._error: Optional[str] = None
        self._duration_ms: float = 0.0
        self._status: str = "pending"

    def initialize(self) -> None:
        """Prepare the agent. Override for custom setup."""
        self._result = {}
        self._error = None
        self._duration_ms = 0.0
        self._status = "pending"

    def validate(self, context: Dict[str, Any]) -> bool:
        """Check if the agent can run given the context.

        Override to add custom validation.
        Returns True if the agent should execute.
        """
        return True

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent logic.

        Args:
            context: Shared context dict with keys like
                     'zone', 'zone_state', 'risk_assessment', etc.

        Returns:
            Dict of results to merge into context and final output.
        """
        ...

    def format_output(self) -> Dict[str, Any]:
        """Format the agent's result for the aggregator."""
        return {
            "agent_name": self.name,
            "agent_type": self.display_name,
            "status": self._status,
            "data": self._result,
            "duration_ms": self._duration_ms,
            "error": self._error,
        }

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with error handling and timing.

        This is the main entry point called by AgentManager.
        It wraps execute() with validation, timing, and error recovery.
        """
        self.initialize()

        # Validate
        if not self.validate(context):
            self._status = "skipped"
            self._error = "Validation failed"
            return self.format_output()

        # Execute with timing
        start = time.time()
        try:
            self._result = await self.execute(context)
            self._status = "completed"
        except Exception as e:
            self._status = "failed"
            self._error = str(e)
            self._result = {}
            logger.exception(
                "Agent %s failed | zone=%s | error=%s",
                self.name, context.get("zone", "?"), e,
            )

        self._duration_ms = round((time.time() - start) * 1000, 2)
        return self.format_output()
