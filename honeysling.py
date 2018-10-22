#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

import asyncssh
from asyncssh import SSHServerProcess, SSHWriter, SSHReader, SSHKey
from asyncssh.connection import SSHConnection, SSHServerConnection


class HoneypotServer(asyncssh.SSHServer):

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._conn: Optional[SSHServerConnection] = None

    def get_peername(self):
        return self._conn.get_extra_info('peername')[0]

    def connection_made(self, conn: SSHServerConnection):
        self.logger.info('SSH connection received from %s.',
                         conn.get_extra_info('peername')[0])
        self._conn = conn

    def connection_lost(self, exc):
        if exc:
            self.logger.error('SSH connection error: %s', exc)
        else:
            self.logger.info('SSH connection closed.')

    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        self.logger.info("User %s (%s) tried password %s", username, self.get_peername(), password)
        return True


def handle_client(process: SSHServerProcess):
    try:
        stdout: SSHWriter = process.stdout
        stderr: SSHWriter = process.stderr
        stdin: SSHReader = process.stdin

        stdout.write('Welcome %s!\n\n' % process.get_extra_info('username'))

    finally:
        process.exit(0)


async def run_server(loop: asyncio.AbstractEventLoop, logger: logging.Logger, port=22):
    config_dir = "config"
    host_key: Optional[SSHKey] = None

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    host_key_file = os.path.join(config_dir, "host_key")
    if os.path.isfile(host_key_file):
        logger.info("Loading host key (%s)...", host_key_file)
        host_key = asyncssh.read_private_key(host_key_file)
    else:
        logger.info("Generating host key (%s)...", host_key_file)
        host_key = asyncssh.generate_private_key("ssh-rsa", key_size=1024)
        host_key.write_private_key(host_key_file)
        host_key.write_public_key("%s.pub" % host_key_file)

    assert host_key

    def server_factory():
        return HoneypotServer(logger)

    logger.info("Running Honeypot on port %s", port)
    server: asyncio.AbstractServer = await asyncssh.create_server(server_factory, port=port,
                                                                  server_host_keys=[host_key],
                                                                  process_factory=handle_client,
                                                                  loop=loop)

    async with server:
        await server.wait_closed()


def main():
    parser = argparse.ArgumentParser(description="Honeypot")
    parser.add_argument("-p", "--port", type=int, help="SSH port", default=22)
    args = parser.parse_args()

    # Logging
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname).8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Disable asyncssh logging
    asyncssh.logging.logger.setLevel(logging.WARNING)

    # Start server
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_server(
        loop=loop,
        logger=logging.getLogger("Pot"),
        port=args.port
    ))


if __name__ == "__main__":
    main()
