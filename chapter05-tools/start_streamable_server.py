from tools_mcp_server import mcp_server


if __name__ == '__main__':
    mcp_server.run(
        transport='streamable-http',
        host='127.0.0.1',
        port=8888,
        log_level='debug',
        path='/streamable'
    )




