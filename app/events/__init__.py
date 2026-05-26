from app.events.base import event_bus
from app.events.invite_event import handle_invite_success
from app.events.record_event import handle_record_created


def register_event_handlers():
    print("===== 注册事件处理器 =====")
    event_bus.subscribe("invite_success", handle_invite_success)
    print("已注册 invite_success 事件")
    event_bus.subscribe("record_created", handle_record_created)
