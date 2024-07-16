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
