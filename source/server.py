from aiohttp import web
import aiofiles
import asyncio
import os.path
import logging
import argparse
import os
from collections import namedtuple


PARAMETERS = {}


async def archivate(request):
    archive_hash = request.match_info['archive_hash']
    full_directory_path = '{0}/{1}'.format(PARAMETERS['photo_directory'], archive_hash)
    if not os.path.exists(full_directory_path):
        return web.HTTPNotFound(text='Архив не существует или был удален.')

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename="{}.zip"'.format(archive_hash)
    await response.prepare(request)

    cmd = 'zip -r - {}'.format(full_directory_path)
    subprocess = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        while True:
            archive_chunk = await subprocess.stdout.readline()
            if not archive_chunk:
                await response.write_eof()
                logging.debug('All chunks have been sent ...')
                return response
            logging.debug('Sending archive chunk ...')
            await response.write(archive_chunk)
            await asyncio.sleep(PARAMETERS['response_delay'])
    except asyncio.CancelledError:
        response.force_close()
        subprocess.send_signal(9)
        logging.debug('Send kill(9) signal for archivator subprocess ...')
        raise


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--logging", action="store_true", help="Enable logging")
    parser.add_argument(
        "-d",
        "--delay",
        action="store",
        help="Enable response delay in seconds(as float), example = 0.01",
        type=float
    )
    parser.add_argument("-p", "--path", action="store", help="Path to photo directory", type=str)
    return parser.parse_args()


def get_environments():
    Environments = namedtuple('Environments', 'delay path')
    environments = Environments(
        delay=os.getenv('RESPONSE_DELAY'),
        path=os.getenv('PHOTO_DIRECTORY_PATH')
    )
    return environments


def set_parameters(envs, args):
    if args.logging:
        logging.basicConfig(level=logging.DEBUG)

    if args.delay:
        PARAMETERS['response_delay'] = args.delay
    elif envs.delay:
        PARAMETERS['response_delay'] = envs.delay
    else:
        PARAMETERS['response_delay'] = 0

    if args.path:
        PARAMETERS['photo_directory'] = args.path
    elif envs.path:
        PARAMETERS['photo_directory'] = envs.path
    else:
        raise NotADirectoryError('Photo directory is not defined!')


if __name__ == '__main__':
    envs = get_environments()
    args = get_arguments()
    set_parameters(envs, args)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
