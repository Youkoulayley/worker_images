# Copyright 2016-2018 The NATS Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import asyncio
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN

async def run(loop):
    # Use borrowed connection for NATS then mount NATS Streaming
    # client on top.
    nc = NATS()
    await nc.connect(io_loop=loop)

    # Start session with NATS Streaming cluster.
    sc = STAN()
    await sc.connect("serieall", "client-123", nats=nc)

    # Synchronous Publisher, does not return until an ack
    # has been received from NATS Streaming.
    await sc.publish("foo", b'hello')
    await sc.publish("foo", b'world')

    total_messages = 0
    future = asyncio.Future(loop=loop)

    async def cb(msg):
        nonlocal future
        nonlocal total_messages
        print("Received a message (seq={}): {}".format(msg.seq, msg.data))
        total_messages += 1
        if total_messages >= 2:
            future.set_result(None)

    # Subscribe to get all messages since beginning.
    sub = await sc.subscribe("foo", start_at='first', cb=cb)
    await asyncio.wait_for(future, 1, loop=loop)

    # Stop receiving messages
    await sub.unsubscribe()

    # Close NATS Streaming session
    await sc.close()

    # We are using a NATS borrowed connection so we need to close manually.
    await nc.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()
