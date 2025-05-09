# mcp-server-demo
Demo PoC MCP server to be used in other PoC

## Devs

```bash
uv venv
uv pip install -r pyproject.toml
# then run it locally
mcp dev server.py
# or alternatively
python server.py
```

Navigate to the URL it showed to test your server.

And then you can test functions such as Templates, and then `get_br_database_query`: 

Pass in this:

```json
{
  "query_filters": [
    {
      "name": "BR_OWNER",
      "value": "John Smith",
      "operator": "="
    }
  ],
  "limit": 100,
  "statuses": []
}
```

### pymssql issues

## pymssql on Mac OSX

`pymssql` has dependency with **FreeTDS**, as such ensure you install it beforehand `brew install freetds`.

After which if you have issues with running the code please do the following: 

```bash
# ensure that the version of python you are trying to install it with matches the python version on your system.
# ex: brew install python@3.12
brew install freetds 
uv pip uninstall pymssql
# Set environment for Apple Silicon
export ARCHFLAGS="-arch arm64"
export HOMEBREW_PREFIX=$(brew --prefix)
export FREETDS_PREFIX=$(brew --prefix freetds)
export OPENSSL_PREFIX=$(brew --prefix openssl@3)

export LDFLAGS="-L$FREETDS_PREFIX/lib -L$OPENSSL_PREFIX/lib"
export CPPFLAGS="-I$FREETDS_PREFIX/include -I$OPENSSL_PREFIX/include"
export PKG_CONFIG_PATH="$FREETDS_PREFIX/lib/pkgconfig:$OPENSSL_PREFIX/lib/pkgconfig"
export PATH="$FREETDS_PREFIX/bin:$OPENSSL_PREFIX/bin:$PATH"
uv pip install --pre --no-binary=pymssql pymssql --no-cache
```

Also you can add to `uv` `pyproject.toml`

```toml
[tool.uv]
no-binary-package = ["pymssql"]
```

After this all should be working.

## Documentation

* [Using this](https://github.com/modelcontextprotocol/python-sdk) as tutorial on how to build the demo.
* [FastMCP documentation](https://gofastmcp.com/servers/context)

