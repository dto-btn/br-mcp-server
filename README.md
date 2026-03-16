# Business Request Server
Demo PoC MCP server to be used in other PoC

## Devs

### Configuration

Before running the server or client, create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and provide your database credentials and Azure OpenAI settings.

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BITS_DB_SERVER` | The hostname or IP address of the SQL Server database. | Yes | `missing.domain` |
| `BITS_DB_USERNAME` | The username for database authentication. | Yes | `missing.username` |
| `BITS_DB_PWD` | The password for database authentication. | Yes | `missing.password` |
| `BITS_DB_DATABASE` | The name of the specific database to connect to. | Yes | `missing.dbname` |
| `HOST` | The host address the MCP server will bind to. | No | `0.0.0.0` |
| `PORT` | The port the MCP server will listen on. | No | `8000` |
| `MCP_SERVER_URL` | The URL where the MCP server is accessible (used by client). | No | `http://127.0.0.1:8000/mcp` |
| `CORS_ALLOW_ORIGINS` | Comma-separated list of origins allowed to bridge to the MCP server. | No | `http://localhost,http://127.0.0.1` |
| `CORS_ALLOW_CREDENTIALS` | Whether to allow credentials (cookies, auth headers) in CORS requests. | No | `false` |
| `AZURE_OPENAI_ENDPOINT`| The endpoint URI for your Azure OpenAI resource (used by client). | Yes (Client) | - |
| `AZURE_OPENAI_VERSION` | The API version for Azure OpenAI. | No | `2024-05-01-preview` |
| `CLIENT_ID` | OAuth2 Client ID for authentication (experimental). | No | - |
| `CLIENT_SECRET` | OAuth2 Client Secret for authentication (experimental). | No | - |
| `REDIRECT_URI` | OAuth2 Redirect URI for authentication (experimental). | No | - |

### Installation

```bash
uv venv
uv pip install -e .
# then run it locally
mcp dev server.py
# or alternatively
python server.py
```

Navigate to the URL it showed to test your server.

And then you can test functions such as Templates, and then `search_business_requests`: 

Pass in this for `query`:

```json
{
  "query_filters": [
    {
      "name": "BR_SHORT_TITLE",
      "value": "Server",
      "operator": "="
    }
  ]
}
```

and for `select_fields`:

```json
{
  "fields": [
    "BR_SHORT_TITLE"
  ]
}
```

And then you can filter on the results via `filter_results`: 

```json
[
  {
    "column": "RPT_GC_ORG_NAME_EN",
    "operator": "contains",
    "value": "Correctional"
  }
]
```

## Running via Docker

```bash
docker build -t mcp-bits:local .
docker run -p 8080:8080 --env-file ./.env --name mcp-bits-container mcp-bits:local
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
uv pip uninstall pymssql
export CFLAGS="-I$(brew --prefix freetds)/include"
export LDFLAGS="-L$(brew --prefix freetds)/lib"
uv pip install "packaging>=24" "setuptools>=54.0" "setuptools_scm[toml]>=8.0" "wheel>=0.36.2" "Cython==3.0.10" "tomli"
uv pip install --pre --no-binary :all: pymssql --no-cache --no-build-isolation
```
## Deployment

### CI/CD

TODO

### Manual

This is how you can deploy manually in Azure via the CLI.

```bash
az webapp deployment source config-local-git \
  --name <WebAppName> \
  --resource-group <ResourceGroupName>
git remote add azure <GitURLFromPreviousStep>
git push azure main
```

## Documentation

* [Using this](https://github.com/modelcontextprotocol/python-sdk) as tutorial on how to build the demo.
* [FastMCP documentation](https://gofastmcp.com/servers/context)
* [MCP OAuth 2.0 Authentication](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)

