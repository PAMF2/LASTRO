"""
Ferramentas para os agentes
"""
from .base import BaseTool
from .monitoring import (
    WhatsAppMonitor,
    PortalMonitor,
    CalendarCheck,
    LeadStatusCheck,
    ImovelMonitor,
)
from .analytics import (
    ConversationAnalyzer,
    DemandAggregator,
    LeadScorer,
    PerformanceCalculator,
    ConversionTracker,
)
from .communication import (
    WhatsAppSender,
    MessageComposer,
    TimingOptimizer,
    ContextLoader,
    MessageTemplates,
    NotificationScheduler,
)

__all__ = [
    "BaseTool",
    # Monitoring
    "WhatsAppMonitor",
    "PortalMonitor",
    "CalendarCheck",
    "LeadStatusCheck",
    "ImovelMonitor",
    # Analytics
    "ConversationAnalyzer",
    "DemandAggregator",
    "LeadScorer",
    "PerformanceCalculator",
    "ConversionTracker",
    # Communication
    "WhatsAppSender",
    "MessageComposer",
    "TimingOptimizer",
    "ContextLoader",
    "MessageTemplates",
    "NotificationScheduler",
]
