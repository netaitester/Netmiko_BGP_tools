# MCP Netmiko Server for Cisco IOS BGP

A lightweight MCP server that uses Netmiko to run read-focused BGP troubleshooting workflows on Cisco IOS routers.

## What This Project Does

This server exposes MCP tools to help operators and automation workflows:
- Check router and BGP health quickly
- Validate expected BGP config intent
- Inspect advertised and received routes
- Troubleshoot missing communities and community policy
- Collect incident evidence in one call

## Available MCP Tools

- `show_ip_interface_brief(router_ip)`
- `show_ip_route(router_ip)`
- `show_bgp_summary_all(router_ips=None, device_type="cisco_ios")`
- `show_bgp_neighbor_detail(router_ip, neighbor_ip, device_type="cisco_ios")`
- `show_bgp_routes_prefix(router_ip, prefix, device_type="cisco_ios")`
- `validate_bgp_config_all(local_as=None, expected_neighbors=None, expected_networks=None, router_ips=None, device_type="cisco_ios")`
- `show_bgp_advertised_routes(router_ip, neighbor_ip, device_type="cisco_ios")`
- `show_bgp_received_routes(router_ip, neighbor_ip, device_type="cisco_ios")`
- `check_bgp_reachability_matrix(router_ips, expected_neighbors=None, device_type="cisco_ios")`
- `collect_bgp_incident_bundle(router_ips=None, device_type="cisco_ios")`
- `show_bgp_community(router_ip, community, device_type="cisco_ios")`
- `show_bgp_community_list(router_ip, community_list, device_type="cisco_ios")`
- `show_bgp_prefix_communities(router_ip, prefix, device_type="cisco_ios")`
- `validate_bgp_community_config(router_ips=None, expected_send_community_neighbors=None, device_type="cisco_ios")`

## Requirements

- Python 3.11+
- Network reachability from host to target Cisco IOS routers
- Valid router credentials available as environment variables

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

The server reads credentials and default target routers from environment variables:

- `NETMIKO_USERNAME`
- `NETMIKO_PASSWORD`
- `NETMIKO_ROUTER_IPS` (comma-separated list, optional when tool input provides targets)

Create a local env file from the template:

```bash
cp .env.example .env
```

Then set your values in `.env`.

## Run the Server

```bash
source venv/bin/activate
python mcp_netmiko_server.py
```

## VS Code MCP Server Config Example

Use a local, untracked config in `.vscode/mcp.json`:

```json
{
  "servers": {
    "MCP-BGP-CISCO-IOS": {
      "type": "stdio",
      "command": "venv/bin/python",
      "cwd": "${workspaceFolder}",
      "env": {
        "NETMIKO_USERNAME": "your-username",
        "NETMIKO_PASSWORD": "your-password",
        "NETMIKO_ROUTER_IPS": "192.168.100.100,192.168.50.20,192.168.50.30"
      },
      "args": ["mcp_netmiko_server.py"]
    }
  }
}
```

## Custom Agent and Skills

This repository includes Copilot customizations under `.github/`:

- Agent: `.github/agents/network-engineer.agent.md`
- Skills:
  - `.github/skills/bgp-troubleshooting/SKILL.md`
  - `.github/skills/bgp-session-down/SKILL.md`
  - `.github/skills/bgp-route-exchange-issues/SKILL.md`
  - `.github/skills/bgp-route-missing-prefix/SKILL.md`

These files provide guided workflows for common BGP incidents and help keep troubleshooting output consistent (scope, evidence, likely cause, next-safe actions).

Use these customizations when:
- BGP sessions are down or unstable
- Sessions are up but route exchange is broken
- One specific prefix is missing end-to-end

## Security Notes

- Do not commit real credentials, router secrets, or production topology details.
- Keep `.vscode/mcp.json` local only.
- Rotate credentials immediately if they were previously committed.

## Suggested Next Improvements

- Add unit tests for input parsing and target resolution logic
- Add CI for lint and tests
- Add typed response models for MCP tool outputs

## License

This project is licensed under the MIT License. See `LICENSE` for details.
