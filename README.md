# MCP Server for Vertex AI Search SSE版

Difyでの実行等を想定し、Fork元ではStdio形式で動作したプログラム (https://github.com/ShintaroMorimoto/vais-mcp) をSSEで動かせるように改修したものです。

- docker-compose.yamlを追加し、docker composeで動かせるようにしました。
- ツール名・補足をツール自体につけ、LLMがツールについて理解しやすくしています。

詳細については、[私のブログ](https://www.bluecore.net/archives/102) を参考にしてください。その他AI関連のネタをぼちぼち書いてます。

以下、Fork元文書を引用しています。

-----

# MCP Server for Vertex AI Search

MCP server to search private data in Vertex AI Search.

## Tools

- `search_vais`: Search for Vertex AI Search and returns result chunks.
  Returns a dictionary with a "response" key. The value of "response" is a list of dictionaries, each containing the title of the source document and the extracted content chunk. Example:

```json
{
  "response": [
    {
      "title": "Sample Document Title 1",
      "content": "Extracted text segment from the document."
    },
    {
      "title": "Sample Document Title 2",
      "content": "Another extracted text segment."
    }
  ]
}
```

## Prerequisites

1. Install uv from [Astral](https://docs.astral.sh/uv/getting-started/installation/) or the [GitHub README](https://github.com/astral-sh/uv#installation)
2. Install Python 3.13 using `uv python install 3.13`
3. Create a Vertex AI Search app  
   i. [Official Document](https://cloud.google.com/generative-ai-app-builder/docs/create-engine-es)

## Configuration

Add the following to your server configuration:

```json
{
  "mcpServers": {
    "vais-mcp": {
      "command": "uvx",
      "args": ["vais-mcp@latest"],
      "env": {
        "GOOGLE_CLOUD_PROJECT_ID": "<google_cloud_project_id>",
        "VAIS_ENGINE_ID": "<vais_engine_id>"
      }
    }
  }
}
```

If you want to run with Docker, you will need to obtain a service account key beforehand and mount its path into the Docker container, configured within your `mcp.json`:

```json
{
  "mcpServers": {
    "vais-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GOOGLE_CLOUD_PROJECT_ID",
        "-e",
        "VAIS_ENGINE_ID",
        "-e",
        "USE_MOUNTED_SA_KEY",
        "-v",
        "/your/local/path/to/sa-key.json:/app/secrets/sa-key.json:ro",
        "mrmtsntr/vais-mcp:latest"
      ],
      "env": {
        "GOOGLE_CLOUD_PROJECT_ID": "<google_cloud_project_id>",
        "VAIS_ENGINE_ID": "<vais_engine_id>",
        "USE_MOUNTED_SA_KEY": "true"
      }
    }
  }
}
```

Note: When using Docker as shown above, ensure the local path `/your/local/path/to/sa-key.json` correctly points to your service account key file.

Note: You can find the Vertex AI Search engine ID in the app url.

```
https://console.cloud.google.com/gen-app-builder/locations/<location>/engines/<engine_id>/overview/system...
```

### Optional Parameters

You can configure the following optional parameters in the environment or server configuration:

- `vais_location`: The location of the Vertex AI Search engine. (Default: "global")
- `page_size`: The number of documents to retrieve as search results. (Default: 5)
- `max_extractive_segment_count`: The maximum number of extractive chunks to retrieve from each document. (Default: 2)
- `log_level`: Specifies the logging level. (Default: "WARNING")
- `IMPERSONATE_SERVICE_ACCOUNT`: The email address of a service account to impersonate for Google Cloud authentication. See the "Google Cloud Authentication" section for details.
- `USE_MOUNTED_SA_KEY`: Set to `true` to indicate that a service account key file is mounted at `/app/secrets/sa-key.json` inside the container and should be used for authentication. (Default: `false`) If `false`, Application Default Credentials (ADC) will be used (unless `IMPERSONATE_SERVICE_ACCOUNT` is set and it also uses a mounted key as its source). If you set this to `true`, you **must** mount your local SA key file to `/app/secrets/sa-key.json` in the Docker container.

Example:

```json
  "env": {
    "GOOGLE_CLOUD_PROJECT_ID": "<google_cloud_project_id>",
    "VAIS_ENGINE_ID": "<vais_engine_id>",
    "VAIS_LOCATION": "us-central1",
    "PAGE_SIZE": "20",
    "MAX_EXTRACTIVE_SEGMENT_COUNT": "8",
    "LOG_LEVEL": "DEBUG",
    "IMPERSONATE_SERVICE_ACCOUNT": "your-sa@project.iam.gserviceaccount.com",
    "USE_MOUNTED_SA_KEY": "true"
  }
```

## Google Cloud Authentication

This MCP server authenticates to Google Cloud using the following methods, taking into account the `IMPERSONATE_SERVICE_ACCOUNT` and `USE_MOUNTED_SA_KEY` environment variables:

- **Service Account Impersonation**:

  - If the `IMPERSONATE_SERVICE_ACCOUNT` environment variable is set to the email address of a target service account, the server will attempt to impersonate that service account.
    - If `USE_MOUNTED_SA_KEY` is `true` (and a service account key file is mounted to `/app/secrets/sa-key.json` in the container), the service account key file at `/app/secrets/sa-key.json` will be used as the source credentials for impersonation.
    - If `USE_MOUNTED_SA_KEY` is `false`, Application Default Credentials (ADC) will be used as the source credentials for impersonation.

- **Direct Authentication (No Impersonation)**:
  - If `IMPERSONATE_SERVICE_ACCOUNT` is **not** set:
    - If `USE_MOUNTED_SA_KEY` is `true` (and a service account key file is mounted to `/app/secrets/sa-key.json`), the server will directly use the service account key file at `/app/secrets/sa-key.json` for authentication.
    - If `USE_MOUNTED_SA_KEY` is `false`, the server will use ADC for authentication.

ADC automatically find credentials from the environment, such as your local user credentials (set up via `gcloud auth application-default login`) or a service account attached to the compute resource. For more details, see the [official documentation](https://cloud.google.com/docs/authentication/provide-credentials-adc).

When using Docker via `mcp.json`:
If you set `USE_MOUNTED_SA_KEY` to `"true"` in the `env` section of your `mcp.json` configuration, and correctly mount your local service account key file to `/app/secrets/sa-key.json` using the `-v` flag within the `args` section, the mounted service account key will be used for authentication as described in the flows above.

**Note:**

- The account used for authentication **must** have the "Discovery Engine Viewer" role (`roles/discoveryengine.viewer`).
  This is required to access Vertex AI Search resources. For more information about roles, see [AI Applications roles and permissions](https://cloud.google.com/generative-ai-app-builder/docs/access-control).

- If you are running locally, you can set up ADC by running:
  ```bash
  gcloud auth application-default login
  ```
- For production environments, it is recommended to use a service account with the minimum required permissions.

## Development

### Building

To prepare this package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

### Debugging

You can launch the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) using following command:

```bash
npx @modelcontextprotocol/inspector uvx vais-mcp@latest GOOGLE_CLOUD_PROJECT_ID=<google_cloud_project_id> VAIS_ENGINE_ID=<vais_engine_id>
```
