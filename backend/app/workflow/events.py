"""Event bus for workflow execution events."""

import asyncio
import json
import logging
from typing import Any, Dict, List
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

class WorkflowEventBus:
    """A lightweight event bus to broadcast workflow execution events to WebSockets."""
    
    def __init__(self):
        # Maps workflow_id to a list of connected asyncio queues
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        
    async def subscribe(self, workflow_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific workflow."""
        if workflow_id not in self.subscribers:
            self.subscribers[workflow_id] = []
        
        queue = asyncio.Queue()
        self.subscribers[workflow_id].append(queue)
        logger.info(f"Subscribed to workflow {workflow_id}. Total subscribers: {len(self.subscribers[workflow_id])}")
        return queue
        
    def unsubscribe(self, workflow_id: str, queue: asyncio.Queue):
        """Unsubscribe from a specific workflow."""
        if workflow_id in self.subscribers:
            if queue in self.subscribers[workflow_id]:
                self.subscribers[workflow_id].remove(queue)
            if not self.subscribers[workflow_id]:
                del self.subscribers[workflow_id]
        logger.info(f"Unsubscribed from workflow {workflow_id}.")

    async def publish(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """Publish an event to all subscribers of a workflow."""
        if workflow_id not in self.subscribers:
            return

        # Build standardized event envelope
        event_payload = {
            "type": event_type,
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **data
        }

        # Handle UUIDs and other non-JSON serializable objects
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat() + "Z"
            if isinstance(obj, UUID):
                return str(obj)
            # Default fallback for models
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "dict"):
                return obj.dict()
            raise TypeError(f"Type {type(obj)} not serializable")

        try:
            json_str = json.dumps(event_payload, default=json_serial)
            queues = self.subscribers[workflow_id]
            for queue in queues:
                # We put the string into the queue
                await queue.put(json_str)
        except Exception as e:
            logger.error(f"Error publishing event to workflow {workflow_id}: {e}")

# Singleton instance
event_bus = WorkflowEventBus()
