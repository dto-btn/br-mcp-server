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

or

```json
{
  "query_filters": [
    {
      "name": "CPLX_EN",
      "value": "High",
      "operator": "="
    }
  ],
  "limit": 100,
  "statuses": []
}
```

## pymssql issues

### pymssql on Mac OSX

`pymssql` has dependency with **FreeTDS**, as such ensure you install it beforehand `brew install freetds`.

After which if you have issues with running the code please do the following: 

```bash
uv pip uninstall pymssql
uv pip install --pre --no-binary :all: pymssql --no-cache --no-build-isolation
```

Also you can add to `uv` `pyproject.toml`

```toml
[tool.uv]
no-binary-package = ["pymssql"]
```

After this all should be working.

NOTE: Known issue with `cython==3.1.0` [found here](https://github.com/pymssql/pymssql/issues/937)

Here is how to get around it for now (please remove this once this issue is fixed):

```bash
export CFLAGS="-I$(brew --prefix freetds)/include"
export LDFLAGS="-L$(brew --prefix freetds)/lib"
uv pip install "packaging>=24" "setuptools>=54.0" "setuptools_scm[toml]>=8.0" "wheel>=0.36.2" "Cython==3.0.10" "tomli"
uv pip install --pre --no-binary :all: pymssql --no-cache --no-build-isolation
```

## Documentation

* [Using this](https://github.com/modelcontextprotocol/python-sdk) as tutorial on how to build the demo.
* [FastMCP documentation](https://gofastmcp.com/servers/context)

