"""Isolated coordinator tests plus a real local aiohttp HTTP server."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from aiohttp import ClientSession, web

ROOT = Path(__file__).resolve().parents[1]
for name in ['homeassistant','homeassistant.util','homeassistant.core','homeassistant.helpers','homeassistant.helpers.update_coordinator']:
    sys.modules[name] = types.ModuleType(name)
sys.modules['homeassistant.util'].dt = types.SimpleNamespace(utcnow=lambda: datetime.now(timezone.utc))
sys.modules['homeassistant.core'].HomeAssistant = object
class Coordinator:
    def __init__(self,*a,**kw): self.last_update_success=True
    async def async_request_refresh(self): self.data=await self._async_update_data()
sys.modules['homeassistant.helpers.update_coordinator'].DataUpdateCoordinator=Coordinator
sys.modules['homeassistant.helpers.update_coordinator'].UpdateFailed=RuntimeError
pkg=types.ModuleType('iotmeter');pkg.__path__=[str(ROOT/'custom_components/iotmeter')];sys.modules['iotmeter']=pkg
from iotmeter.coordinator import IoTMeterCoordinator
import iotmeter.coordinator as module

class PollingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now=100.0;self.calls=[];self.sessions=[];self.payload={'ID':'93189','NUMBER_OF_EVSE':2,'EV_STATE':[1,3]}
        self.c=IoTMeterCoordinator(None,'127.0.0.1');self.c._clock=lambda:self.now
        async def fetch(session,endpoint):
            self.calls.append(endpoint);self.sessions.append(session)
            return dict(self.payload) if self.payload is not None else None
        self.c._fetch_json=fetch
    async def tick(self,seconds=0):
        self.now+=seconds;self.calls=[];self.c.data=await self.c._async_update_data();return self.calls
    async def test_intervals_and_sessions(self):
        self.assertEqual(await self.tick(),['/updateSetting','/updateEvse','/updateData'])
        first=self.sessions[-1];old=self.c.last_success['evse']
        self.assertTrue(first.closed)
        self.assertEqual(await self.tick(5),['/updateData'])
        self.assertIs(self.c.last_success['evse'],old)
        self.assertIsNot(first,self.sessions[-1]);self.assertTrue(self.sessions[-1].closed)
        self.assertEqual(await self.tick(5),['/updateEvse','/updateData'])
        self.assertEqual(await self.tick(50),['/updateSetting','/updateEvse','/updateData'])
    async def test_failed_source_stays_failed_until_attempt(self):
        await self.tick();old=self.c.last_success['evse'];self.payload=None
        await self.tick(10);self.assertFalse(self.c.source_success['evse']);self.assertIs(self.c.last_success['evse'],old)
        self.payload={'ID':'93189'};await self.tick(5)
        self.assertFalse(self.c.source_success['evse']);self.assertTrue(self.c.source_success['data'])
        self.assertEqual(await self.tick(1),[])
    async def test_write_refresh_settings(self):
        await self.tick();self.calls=[];await self.c.async_request_settings_refresh()
        self.assertEqual(self.calls,['/updateSetting'])
    async def test_invalid_device_id(self):
        self.payload={'ID':'other'};await self.tick()
        self.assertFalse(self.c.source_success['settings']);self.assertFalse(self.c.source_success['data'])
    async def test_cancellation_closes_session(self):
        async def cancel(session,endpoint):
            self.sessions.append(session);raise asyncio.CancelledError()
        self.c._fetch_json=cancel
        with self.assertRaises(asyncio.CancelledError):await self.tick()
        self.assertTrue(self.sessions[-1].closed)
    async def test_real_http_new_connection_between_batches(self):
        transports=[];active=0;peak=0
        async def handler(request):
            nonlocal active,peak
            active+=1;peak=max(peak,active);transports.append(request.transport)
            await asyncio.sleep(.005);active-=1
            return web.json_response({'ID':'93189'})
        app=web.Application();app.router.add_get('/{endpoint}',handler)
        runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
        try:
            self.c.base_url='http://127.0.0.1:'+str(site._server.sockets[0].getsockname()[1])
            self.c._fetch_json=types.MethodType(IoTMeterCoordinator._fetch_json,self.c)
            await self.tick();first=transports[-1];await self.tick(5)
            self.assertEqual(peak,1);self.assertIsNot(first,transports[-1])
        finally:await runner.cleanup()

if __name__=='__main__':unittest.main(verbosity=2)
