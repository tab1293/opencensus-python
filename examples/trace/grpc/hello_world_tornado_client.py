# Copyright 2017, OpenCensus Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import grpc

import hello_world_pb2
import hello_world_pb2_grpc

from opencensus.trace.tracer import Tracer
from opencensus.trace.exporters import stackdriver_exporter
from opencensus.trace.ext.grpc import client_interceptor

import tornado.ioloop
import tornado.gen

from datetime import timedelta

HOST_PORT = 'localhost:50051'


def _grpc_tornado_future_callback(tornado_future, grpc_future):
    try:
        tornado_future.set_result(grpc_future.result())
    except Exception as e:
        tornado_future.set_exception(e)

def _grpc_tornado_future(grpc_future):
    """
        Wraps a GRPC result in a future that can be yielded by tornado
    """
    tornado_future = tornado.gen.Future()
    tornado_ioloop =  tornado.ioloop.IOLoop.current()
    grpc_future.add_done_callback(lambda _: tornado_ioloop.add_callback(_grpc_tornado_future_callback, tornado_future, grpc_future))
    return tornado_future

@tornado.gen.coroutine
def yield_future(future):
    resp = yield future
    print(resp)

def main():
    exporter = stackdriver_exporter.StackdriverExporter()
    tracer = Tracer(exporter=exporter)
    tracer_interceptor = client_interceptor.OpenCensusClientInterceptor(
        tracer,
        host_port=HOST_PORT)
    channel = grpc.insecure_channel(HOST_PORT)
    channel = grpc.intercept_channel(channel, tracer_interceptor)
    stub = hello_world_pb2_grpc.GreeterStub(channel)

    ioloop = tornado.ioloop.IOLoop.instance()
    for i in range(5):
        future = stub.SayHello.future(hello_world_pb2.HelloRequest(name='you'))
        tornado_future = _grpc_tornado_future(future)
        ioloop.add_timeout(timedelta(seconds=i), lambda: yield_future(tornado_future))

    ioloop.start()

if __name__ == '__main__':
    main()
