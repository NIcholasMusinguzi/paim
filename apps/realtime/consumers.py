from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.events import now_iso


class ParishConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.parish_id = int(self.scope["url_route"]["kwargs"]["parish_id"])
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return await self.close(code=4401)
        if not await self.may_view(user, self.parish_id):
            return await self.close(code=4403)  # scoping, same rule as HTTP
        self.group = f"parish.{self.parish_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "hello", "server_time": now_iso()})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def domain_event(self, message):
        await self.send_json(message["payload"])

    @database_sync_to_async
    def may_view(self, user, parish_id) -> bool:
        from apps.accounts.scoping import parish_ids_for

        return parish_ids_for(user).filter(id=parish_id).exists()


class ScopeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.level = self.scope["url_route"]["kwargs"]["level"]
        scope_id_raw = self.scope["url_route"]["kwargs"]["scope_id"]
        self.scope_id = int(scope_id_raw) if scope_id_raw else None
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return await self.close(code=4401)
        if not await self.may_view(user, self.level, self.scope_id):
            return await self.close(code=4403)
        self.group = f"scope.{self.level}.{self.scope_id or ''}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "hello", "server_time": now_iso()})

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def domain_event(self, message):
        await self.send_json(message["payload"])

    @database_sync_to_async
    def may_view(self, user, level, scope_id) -> bool:
        from apps.accounts.models import Role

        if user.role == Role.NATIONAL_ADMIN:
            return True
        if level == "district":
            return user.scope_level == "district" and user.scope_id == scope_id
        return False
