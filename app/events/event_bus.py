from typing import Dict, List, Callable, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventBus:
    _handlers: Dict[str, List[Callable]] = {}
    _lock = asyncio.Lock()
    
    @classmethod
    def subscribe(cls, event_name: str, handler: Callable):
        """订阅事件处理函数"""
        if event_name not in cls._handlers:
            cls._handlers[event_name] = []
        if handler not in cls._handlers[event_name]:
            cls._handlers[event_name].append(handler)
            logger.debug(f"Handler subscribed to event: {event_name}")
    
    @classmethod
    def unsubscribe(cls, event_name: str, handler: Callable):
        """取消订阅事件处理函数"""
        if event_name in cls._handlers:
            cls._handlers[event_name].remove(handler)
            logger.debug(f"Handler unsubscribed from event: {event_name}")
    
    @classmethod
    async def publish(cls, event_name: str, data: Any):
        """发布事件，通知所有订阅者"""
        if event_name not in cls._handlers:
            return
        
        handlers = cls._handlers[event_name]
        logger.debug(f"Publishing event: {event_name}, handlers: {len(handlers)}")
        
        async with cls._lock:
            for handler in handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error handling event {event_name}: {e}")
    
    @classmethod
    def get_subscribed_events(cls) -> List[str]:
        """获取所有已订阅的事件名称"""
        return list(cls._handlers.keys())
    
    @classmethod
    def get_handler_count(cls, event_name: str) -> int:
        """获取指定事件的处理函数数量"""
        return len(cls._handlers.get(event_name, []))