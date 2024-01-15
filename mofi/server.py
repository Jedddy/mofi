import asyncio
import json
from collections import defaultdict
from typing import Any, Callable, Literal

import uvicorn
from fastapi import APIRouter, FastAPI, Request, HTTPException

from .schemas import GlobalType, Donation, ShopOrder, Subscription


types = {
    "global": GlobalType,
    "donation": Donation,
    "subscription": Subscription,
    "shop_order": ShopOrder,
}


class Mofi:
    """The class to handle Ko-fi webhooks."""

    _app: FastAPI | APIRouter

    def __init__(self, token: str):
        self.token = token
        self._app = FastAPI(title="Mofi")
        self._callbacks: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def run(self, *, host: str = "127.0.0.1", port: int = 8000):
        """Run the server."""

        self._setup()
        uvicorn.run(self._app, host=host, port=port)

    def as_router(self) -> APIRouter:
        """Converts the app to a FastAPI Router."""

        self._app = APIRouter(tags=["Mofi"])
        self._setup()
        return self._app

    def _setup(self):
        @self._app.post("/")
        async def _(data: Request):
            valid = True
            r = await data.form()

            try:
                rjson = json.loads(r["data"])
                ptype: str = rjson["type"]
                payload_type = ptype.lower().replace(" ", "_")

                if (
                    rjson["verification_token"] != self.token
                    or payload_type not in types
                ):
                    valid = False

            except (json.JSONDecodeError, KeyError):
                valid = False

            if not valid:
                raise HTTPException(400, detail="Invalid request")

            schema = types[payload_type]
            callbacks = self._callbacks[payload_type] or self._callbacks["global"]

            for cb in callbacks:
                if asyncio.iscoroutinefunction(cb):
                    await cb(schema(**rjson))
                else:
                    cb(schema(**rjson))

    def callback(
        self,
        type: Literal["global", "donation", "subscription", "shop_order"],
    ):
        """A decorator to add a callback for a webhook type.

        Args:
            type (str): The type to listen listen to
        """

        def wrapper(func: Callable[..., Any]):
            self._callbacks[type.lower()].append(func)

        return wrapper
