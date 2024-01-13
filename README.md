# Mofi

A simple webhook wrapper for [Ko-fi](https://ko-fi.com)

Mofi uses [FastAPI](https://fastapi.tiangolo.com/) to handle the webhooks.

## Installation

```bash
$ pip install mofi
```

## Usage

```python
from mofi import Mofi, Donation, GlobalType, Subscription, ShopOrder

app = Mofi(token="token")


@app.callback("donation")
async def donation(data: Donation):
    print("Donation event.")


@app.callback("subscription")
async def subscription(data: Subscription):
    print("Subscription event")


@app.callback("shop_order")
async def shop_order(data: ShopOrder):
    print("Shop Order event")


@app.callback("global")
async def global_callback(data: GlobalType):
    print("Global event")  # matches all event types


app.run(host="127.0.0.1", port=8000)  # use 0.0.0.0 and 80 on deployment
```
To get your token, go [here](https://ko-fi.com/manage/webhooks) and click "Advanced"

To test, use ngrok or similar to expose your local server to the internet.
```
$ ngrok http 8000
```

Then, set your webhook url to the ngrok url and you should see the events in your console.
