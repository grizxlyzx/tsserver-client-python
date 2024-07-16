# TSServer Client Python
Python client for `tsserver`

## Description
To inspect and manipulate code, a common approach is to use **Abstract Syntax Tree (AST)** tools, like `tree-sitter`, to structure the code and modify it at a low level. Additionally, the **Language Server Protocol (LSP)**, which often leverages AST, is used for language-specific inspection and semantic diagnostics at the repository level.

For TypeScript, `tsserver` is the official language server. It underlies most editor's TypeScript plugins, though it is [NOT LSP-compatible](https://github.com/microsoft/TypeScript/issues/39459) by itself.

This project implements a `tsserver` client in Python and exposes some commonly used methods to interact with `tsserver`.

## Usage
### Prerequisite
1. Ensure that `node` and `tsserver` are correctly installed on your system.
2. Set environment variable `TSSERVER_PATH` to `/path/to/tsserver.js` or configure it in `config.py`.

### Installation
```
git clone https://github.com/grizxlyzx/tsserver-client-python.git
cd /project/root/directoy/
pip install .
```

### Example Usage
```python
import asyncio
from tsserver_client import TSServerClient

async def main():
    f_path = '/path/to/your/code.tsx'
    out = {}
    # edit line and offset numbers in the arguments
    async with TSServerClient.create_on_file(f_path) as tss:
        out['definition'] = await tss.cmd_goto_definition(f_path, 149, 12)
        out['completions'] = await tss.cmd_completions(f_path, 159, 1, prefix='ex')
        out['signature'] = await tss.cmd_signature_help(f_path, 47, 11)
        out['modi_instruct'] = await tss.cmd_organize_imports(f_path)
        out['references'] = await tss.cmd_references(f_path, 14, 7)
        out['type_define'] = await tss.cmd_goto_type_definition(f_path, 8, 10)
        out['errors'] = await tss.cmd_get_errors([f_path])
        out['reload_done'] = await tss.cmd_reload(f_path)
        out['quickinfo'] = await tss.cmd_quick_info(f_path, 58, 15)
        out['project_errors'] = await tss.cmd_get_errors_for_project(f_path)
    print('done')
    for k, v in out.items():
        print(f'==={k}===\n{v}\n')


if __name__ == '__main__':
    asyncio.run(main())

```

## See Also

https://github.com/microsoft/TypeScript/blob/main/src/server/protocol.ts
https://github.com/microsoft/TypeScript-Sublime-Plugin/tree/master
https://github.com/microsoft/monitors4codegen/tree/main/src/monitors4codegen/multilspy