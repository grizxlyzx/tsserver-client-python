import asyncio
from contextlib import asynccontextmanager
from .comm import TSServerComm, TSServerStopLoopException, TSServerEvent
from .config import *
from typing import (
    Union,
    AsyncIterator
)


class TSServerClient(TSServerComm):
    def __init__(
            self,
            ts_server_proc: asyncio.subprocess.Process
    ):
        super().__init__(ts_server_proc)

    @classmethod
    async def start(cls) -> 'TSServerClient':
        cmd = 'node' + ' ' + TSSERVER_PATH
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        ts_server = cls(proc)
        return ts_server

    async def stop(self):
        proc = self._tsserver_proc
        proc.stdout.set_exception(TSServerStopLoopException())
        await self.send_request('exit', None, None)
        # TODO: cleanup everything else
        for _, task in self._tasks.items():
            task.cancel()
        self._tsserver_proc = None

    @classmethod
    @asynccontextmanager
    async def create_on_file(
            cls,
            file_path: str
    ) -> AsyncIterator['TSServerClient']:
        self = await cls.start()
        # TODO: send init requests to TSServer
        await self.cmd_configure()
        # await self.cmd_compiler_options_for_inferrd_project()
        await self.cmd_open(file_path)
        yield self
        await self.stop()

    async def cmd_configure(self, **kwargs) -> bool:
        args = {
            "hostInfo": "tsserver-client-python",
            "preferences": {
                "providePrefixAndSuffixTextForRename": True,
                "allowRenameOfImportPath": True,
                "includePackageJsonAutoImports": "auto",
                "excludeLibrarySymbolsInNavTo": True
            },
            "watchOptions": {}
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='configure',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        return resp.success

    async def cmd_compiler_options_for_inferrd_project(self, **kwargs) -> bool:
        args = {
            "options": {
                "module": "ESNext",
                "moduleResolution": "Bundler",
                "target": "ES2020",
                "jsx": "react",
                "allowImportingTsExtensions": True,
                "strictNullChecks": True,
                "strictFunctionTypes": True,
                "sourceMap": True,
                "allowJs": True,
                "allowSyntheticDefaultImports": True,
                "allowNonTsExtensions": True,
                "resolveJsonModule": True
            }
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='compilerOptionsForInferredProjects',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        return resp.success

    async def cmd_open(
            self,
            path: str,
            **kwargs
    ) -> None:
        args = {
            'file': path
        }
        args.update(kwargs)
        await self.send_request(
            cmd='open',
            expect_output=None,
            arguments=args
        )
        return None

    async def cmd_close(
            self,
            path: str,
            **kwargs
    ) -> None:
        args = {
            'file': path
        }
        args.update(kwargs)
        await self.send_request(
            cmd='close',
            expect_output=None,
            arguments=args
        )

    async def cmd_reload(
            self,
            path: str,
            alternate_path: Union[None, str] = None,
            **kwargs
    ) -> bool:
        args = {
            'file': path,
            'tmpfile': alternate_path if alternate_path else path
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='reload',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        return resp.success

    async def cmd_completions(
            self,
            path: str,
            line: int,
            offset: int,
            prefix: int = '',
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset,
            'prefix': prefix
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='completions',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_signature_help(
            self,
            path: str,
            line: int,
            offset: int,
            prefix: str = '',
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset,
            'prefix': prefix
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='signatureHelp',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_organize_imports(self, path: str) -> Union[None, dict]:
        args = {
            "scope": {
                "type": "file",
                "args": {
                    "file": path
                }
            },
        }
        _, handler = await self.send_request(
            cmd='organizeImports',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_references(
            self,
            path: str,
            line: int,
            offset: int,
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='references',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_goto_definition(
            self,
            path: str,
            line: int,
            offset: int,
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='definition',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_goto_type_definition(
            self,
            path: str,
            line: int,
            offset: int,
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='definition',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret

    async def cmd_get_errors(
            self,
            path_list: list[str],
            delay: int = 0,  # ms
            **kwargs
    ) -> Union[None, dict]:
        """
        Geterr request; value of command field is "geterr". Wait for
        delay milliseconds and then, if during the wait no change or
        reload messages have arrived for the first file in the files
        list, get the syntactic errors for the file, field requests,
        and then get the semantic errors for the file.  Repeat with a
        smaller delay for each subsequent file on the files list.  Best
        practice for an editor is to send a file list containing each
        file that is currently visible, in most-recently-used order.
        :param path_list:
        :param delay:
        :return:
        """

        args = {
            'files': path_list,
            'delay': delay
        }
        args.update(kwargs)
        req, handler = await self.send_request(
            cmd='geterr',
            expect_output='event',
            arguments=args
        )
        ret = []
        req_complete = False
        while not req_complete:
            resp: TSServerEvent = await handler.wait_output()
            if (resp.event in ('syntaxDiag', 'semanticDiag', 'suggestionDiag') and
                    (diagnostics := resp.body.get('diagnostics', None))):
                etc = {
                    'file': resp.body.get('file', ''),
                    'diag': resp.event[:-4]
                }
                ret += [diag | etc for diag in diagnostics]
            elif resp.is_request_completed(req.seq):
                req_complete = True
            else:
                pass
        self._output_handler_registry.deregister_handler(handler)
        return ret if ret else None

    async def cmd_get_errors_for_project(
            self,
            path: str,
            delay: int = 0,  # ms
            **kwargs
    ) -> Union[None, dict]:
        """
        It works similarly with 'Geterr', only
        it request for every file in this project.
        :param path: str, the path to the file requesting project error list.
        :param delay: int, Delay in milliseconds to wait before starting to compute
                      errors for the files in the file list.
        :return: body dict of GetErrForProjectResponse if success, else None.
        """
        args = {
            'file': path,
            'delay': delay
        }
        args.update(**kwargs)
        req, handler = await self.send_request(
            cmd='geterrForProject',
            expect_output='event',
            arguments=args
        )
        ret = []
        req_complete = False
        while not req_complete:
            resp: TSServerEvent = await handler.wait_output()
            if (resp.event in ('syntaxDiag', 'semanticDiag', 'suggestionDiag') and
                    (diagnostics := resp.body.get('diagnostics', None))):
                etc = {
                    'file': resp.body.get('file', ''),
                    'diag': resp.event[:-4]
                }
                ret += [diag | etc for diag in diagnostics]
            elif resp.is_request_completed(req.seq):
                req_complete = True
            else:
                pass
        self._output_handler_registry.deregister_handler(handler)
        return ret if ret else None

    async def cmd_quick_info(
            self,
            path: str,
            line: int,
            offset: int,
            **kwargs
    ) -> Union[None, dict]:
        args = {
            'file': path,
            'line': line,
            'offset': offset
        }
        args.update(kwargs)
        _, handler = await self.send_request(
            cmd='quickinfo',
            expect_output='response',
            arguments=args
        )
        resp = await handler.wait_output()
        ret = None
        if resp.success:
            ret = resp.body
        self._output_handler_registry.deregister_handler(handler)
        return ret
