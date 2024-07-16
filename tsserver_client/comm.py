import json
import asyncio
from dataclasses import dataclass, field
from typing import (
    Literal,
    Union,
    Tuple
)


class TSServerStopLoopException(Exception):
    ...


class TSServerProcessException(Exception):
    ...


class TSServerMessageParseException(Exception):
    ...


@dataclass
class TSServerRequest:
    seq: int
    type: str = field(init=False, default='request')
    command: str
    arguments: dict[str, str] | None

    def __str__(self):
        return json.dumps({
            'seq': self.seq,
            'type': self.type,
            'command': self.command,
            'arguments': self.arguments
        }) + '\n'

    def __bytes__(self):
        return bytes(str(self), 'utf-8')


@dataclass
class TSServerOutputBody:
    seq: int
    type: Literal['event', 'response']

    @staticmethod
    def from_bytes(b_str: bytes) -> Union['TSServerResponse', 'TSServerEvent', None]:
        try:
            body_dict = json.loads(b_str)
            body_type = body_dict.get('type', None)
            if body_type == 'response':
                return TSServerResponse(
                    seq=body_dict['seq'],
                    command=body_dict['command'],
                    request_seq=body_dict['request_seq'],
                    success=body_dict['success'],
                    message=body_dict.get('message', None),
                    body=body_dict.get('body', None),
                    metadata=body_dict.get('metadata', None)
                )
            elif body_type == 'event':
                return TSServerEvent(
                    seq=body_dict['seq'],
                    event=body_dict['event'],
                    body=body_dict.get('body', None)
                )
            else:
                raise TSServerMessageParseException
        except (
                IOError,
                UnicodeDecodeError,
                json.JSONDecodeError,
                TSServerMessageParseException
        ) as e:
            print(e)
            return None


@dataclass
class TSServerResponse(TSServerOutputBody):
    type: str = field(default='response', init=False)
    command: str
    request_seq: int
    success: bool
    message: None | str
    body: any
    metadata: any


@dataclass
class TSServerEvent(TSServerOutputBody):
    type: str = field(default='event', init=False)
    event: str
    body: any

    def is_request_completed(self, req_seq: int) -> bool:
        if self.event == 'requestCompleted':
            if self.body['request_seq'] == req_seq:
                return True
        return False


@dataclass
class TSServerOutputHandler:
    request_seq: int
    _output_buf: asyncio.Queue[Union[TSServerResponse | TSServerEvent]] = field(init=False,
                                                                                default_factory=asyncio.Queue)

    async def push(self, output_body: Union[TSServerResponse | TSServerEvent]):
        await self._output_buf.put(output_body)

    async def wait_output(self) -> Union[TSServerResponse | TSServerEvent]:
        return await self._output_buf.get()


@dataclass
class OutputHandlerRegistry:
    _response_handlers: dict[int, TSServerOutputHandler] = field(default_factory=dict)
    _event_handlers: dict[int, TSServerOutputHandler] = field(default_factory=dict)

    def register_handler(
            self,
            trigger_by: Literal['response', 'event', 'all'],
            handler: TSServerOutputHandler
    ):
        request_seq = handler.request_seq
        if trigger_by in ('response', 'all'):
            self._response_handlers.update({request_seq: handler})
        if trigger_by in ('event', 'all'):
            self._event_handlers.update({request_seq: handler})

    def deregister_handler(
            self,
            handler: TSServerOutputHandler
    ):
        request_seq = handler.request_seq
        self._response_handlers.pop(request_seq, None)
        self._event_handlers.pop(request_seq, None)

    async def on_output(
            self,
            output_body: Union['TSServerResponse', 'TSServerEvent']
    ):
        if output_body.type == 'response':
            request_seq = output_body.request_seq
            handler: TSServerOutputHandler | None = self._response_handlers.get(request_seq, None)
            if handler:
                await handler.push(output_body)

        elif output_body.type == 'event':
            for _, handler in self._event_handlers.items():
                await handler.push(output_body)
                # handler.trigger.set()

        else:
            raise RuntimeError(f'Error: Unknown Output Type: "{output_body.type}"')


class TSServerComm:
    _CONTENT_LENGTH_HEADER = b'Content-Length: '

    def __init__(
            self,
            ts_server_proc: asyncio.subprocess.Process
    ):
        self._tsserver_proc: asyncio.subprocess.Process | None = ts_server_proc
        self._seq: int = 0
        self._output_handler_registry: OutputHandlerRegistry = OutputHandlerRegistry()
        self._tasks: dict[str: asyncio.Task] = dict({
            'watching_response': asyncio.create_task(self._monitor_output())
        })

    @property
    def _inc_seq(self):
        seq = self._seq
        self._seq += 1
        return seq

    async def send_request(
            self,
            cmd: str,
            expect_output: Union[None, Literal['response', 'event', 'all']],
            arguments: Union[None, dict] = None
    ) -> Tuple[TSServerRequest, Union[None, TSServerOutputHandler]]:
        request = TSServerRequest(
            seq=self._inc_seq,
            command=cmd,
            arguments=arguments
        )
        output_handler = None
        if expect_output:
            output_handler = TSServerOutputHandler(request.seq)
            self._output_handler_registry.register_handler(
                trigger_by=expect_output,
                handler=output_handler
            )
        self._tsserver_proc.stdin.write(bytes(request))
        await self._tsserver_proc.stdin.drain()
        return request, output_handler

    async def _monitor_output(self):
        try:
            is_running = lambda: (
                    self._tsserver_proc and
                    self._tsserver_proc.stdout and
                    not self._tsserver_proc.stdout.at_eof()
            )

            body_length = 0
            while is_running():
                if body_length == 0:  # expecting a line of header
                    b_header = await self._tsserver_proc.stdout.readline()
                    b_header = b_header.strip()
                    if b_header and b_header.startswith(TSServerComm._CONTENT_LENGTH_HEADER):
                        body_length = int(b_header[len(TSServerComm._CONTENT_LENGTH_HEADER):])
                elif body_length >= 0:  # expecting to read a body
                    b_body = await self._tsserver_proc.stdout.read(body_length + 1)  # plus 1 for '\n'
                    body_length = 0
                    output_body = TSServerOutputBody.from_bytes(b_body)
                    if output_body:
                        await self._output_handler_registry.on_output(output_body)
                else:
                    continue

        except (
                BrokenPipeError,
                ConnectionResetError,
                TSServerStopLoopException,
                TSServerProcessException
        ):
            pass
        return
