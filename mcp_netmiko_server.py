import os
import ipaddress
from typing import Any
from netmiko import ConnectHandler
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP-BGP-CISCO-IOS")


def _load_credentials() -> tuple[str, str]:
    """
    Load router credentials strictly from environment variables.
    These are expected to be injected from .vscode/mcp.json server env.
    """
    env_username = os.getenv("NETMIKO_USERNAME")
    env_password = os.getenv("NETMIKO_PASSWORD")
    if env_username and env_password:
        return env_username, env_password

    raise RuntimeError(
        "Missing router credentials. Set NETMIKO_USERNAME and NETMIKO_PASSWORD "
        "in MCP server env (for example in .vscode/mcp.json)."
    )


def _parse_router_ips(value: str | list[str]) -> list[str]:
    """
    Parse a single IP, comma-separated string, or list into unique router IPs.
    """
    if isinstance(value, str):
        tokens = [token.strip() for token in value.split(",") if token.strip()]
    else:
        tokens = [str(token).strip() for token in value if str(token).strip()]

    if not tokens:
        return []

    hosts = []
    seen = set()
    for token in tokens:
        ipaddress.ip_address(token)
        if token in seen:
            continue
        seen.add(token)
        hosts.append(token)
    return hosts


def _load_default_router_ips() -> list[str]:
    """
    Load default router IP targets from NETMIKO_ROUTER_IPS env.
    """
    raw = os.getenv("NETMIKO_ROUTER_IPS", "")
    if not raw.strip():
        return []
    return _parse_router_ips(raw)


def _resolve_router_target(router_ip: str) -> tuple[str, str]:
    """
    Accept a router IP.
    """
    value = router_ip.strip()
    ipaddress.ip_address(value)
    return value, value


def _resolve_router_targets(router_ips: str | list[str] | None = None) -> list[tuple[str, str]]:
    """
    Accept None, a single IP, comma-separated IPs, or a list.
    - None: use NETMIKO_ROUTER_IPS from MCP server env
    """
    if router_ips is None:
        default_hosts = _load_default_router_ips()
        if not default_hosts:
            raise RuntimeError(
                "No router targets provided. Set NETMIKO_ROUTER_IPS in MCP server env "
                "or pass router_ips to the tool."
            )
        return [(host, host) for host in default_hosts]

    tokens = _parse_router_ips(router_ips)

    if not tokens:
        raise ValueError("router_ips is empty. Provide one or more router IPs.")

    resolved = []
    seen_hosts = set()
    for token in tokens:
        label, host = _resolve_router_target(token)
        if host in seen_hosts:
            continue
        seen_hosts.add(host)
        resolved.append((label, host))
    return resolved


def _build_router(host: str, device_type: str = "cisco_ios") -> dict:
    """
    Use shared credentials from env or .vscode/mcp.json.
    """
    username, password = _load_credentials()
    return {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
    }


def _run_show(host: str, command: str, device_type: str = "cisco_ios") -> str:
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        return conn.send_command(command)
    finally:
        conn.disconnect()


@mcp.tool()
def show_ip_interface_brief(router_ip: str) -> str:
    """
    Accept router IP.
    """
    _, host = _resolve_router_target(router_ip)
    return _run_show(host, "show ip interface brief")


@mcp.tool()
def show_ip_route(router_ip: str) -> str:
    """
    Accept router IP.
    """
    _, host = _resolve_router_target(router_ip)
    return _run_show(host, "show ip route")

@mcp.tool()
def show_bgp_summary_all(
    router_ips: str | list[str] | None = None,
    device_type: str = "cisco_ios",
) -> list[dict]:
    """
    Collect "show ip bgp summary" from one or multiple routers.
    """
    results = []

    for name, host in _resolve_router_targets(router_ips):
        conn = None
        try:
            conn = ConnectHandler(**_build_router(host, device_type))
            summary_output = conn.send_command("show ip bgp summary")
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "ok",
                    "bgp_summary": summary_output,
                }
            )
        except Exception as e:
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "error",
                    "error": str(e),
                }
            )
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass

    return results


@mcp.tool()
def show_bgp_neighbor_detail(
    router_ip: str,
    neighbor_ip: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show detailed BGP neighbor information on one router.
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        detail_output = conn.send_command(f"show ip bgp neighbors {neighbor_ip}")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "neighbor_ip": neighbor_ip,
            "bgp_neighbor_detail": detail_output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def show_bgp_routes_prefix(
    router_ip: str,
    prefix: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show BGP route details for a specific prefix on one router.
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        route_output = conn.send_command(f"show ip bgp {prefix}")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "prefix": prefix,
            "bgp_route_output": route_output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def validate_bgp_config_all(
    local_as: int | None = None,
    expected_neighbors: dict[str, list[dict[str, Any]]] | None = None,
    expected_networks: dict[str, list[dict[str, str]]] | None = None,
    router_ips: str | list[str] | None = None,
    device_type: str = "cisco_ios",
) -> list[dict]:
    """
    Validate BGP configuration and basic state on all routers.

    Optional expectations:
    - local_as: expected local ASN for all routers
    - expected_neighbors: {"192.168.100.100": [{"ip": "10.0.12.2", "remote_as": 65000}]}
    - expected_networks: {"192.168.100.100": [{"prefix": "192.168.1.0", "mask": "255.255.255.0"}]}
    """
    results = []
    expected_neighbors = expected_neighbors or {}
    expected_networks = expected_networks or {}

    for name, host in _resolve_router_targets(router_ips):
        conn = None
        try:
            conn = ConnectHandler(**_build_router(host, device_type))
            bgp_config = conn.send_command("show run | section router bgp")
            bgp_summary = conn.send_command("show ip bgp summary")
            ip_route = conn.send_command("show ip route")

            issues = []
            checks = {
                "bgp_process_present": "router bgp" in bgp_config,
                "asn_matches": None,
                "missing_neighbor_lines": [],
                "missing_network_lines": [],
            }

            if not checks["bgp_process_present"]:
                issues.append("Missing BGP process in running config")

            if local_as is not None:
                asn_line = f"router bgp {local_as}"
                checks["asn_matches"] = asn_line in bgp_config
                if not checks["asn_matches"]:
                    issues.append(f"Expected local ASN not found: {local_as}")

            for neighbor in expected_neighbors.get(name, []):
                neighbor_line = f"neighbor {neighbor['ip']} remote-as {neighbor['remote_as']}"
                if neighbor_line not in bgp_config:
                    checks["missing_neighbor_lines"].append(neighbor_line)
                    issues.append(f"Missing neighbor statement: {neighbor_line}")

            for network in expected_networks.get(name, []):
                network_line = f"network {network['prefix']} mask {network['mask']}"
                if network_line not in bgp_config:
                    checks["missing_network_lines"].append(network_line)
                    issues.append(f"Missing network statement: {network_line}")

            status = "ok" if not issues else "fail"
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": status,
                    "checks": checks,
                    "issues": issues,
                    "bgp_config": bgp_config,
                    "bgp_summary": bgp_summary,
                    "ip_route": ip_route,
                }
            )
        except Exception as e:
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "error",
                    "error": str(e),
                }
            )
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass

    return results


@mcp.tool()
def show_bgp_advertised_routes(
    router_ip: str,
    neighbor_ip: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show routes advertised to a specific BGP neighbor.
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        output = conn.send_command(f"show ip bgp neighbors {neighbor_ip} advertised-routes")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "neighbor_ip": neighbor_ip,
            "advertised_routes": output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def show_bgp_received_routes(
    router_ip: str,
    neighbor_ip: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show routes received from a specific BGP neighbor.
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        output = conn.send_command(f"show ip bgp neighbors {neighbor_ip} routes")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "neighbor_ip": neighbor_ip,
            "received_routes": output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def check_bgp_reachability_matrix(
    router_ips: str | list[str],
    expected_neighbors: dict[str, list[str]] | None = None,
    device_type: str = "cisco_ios",
) -> list[dict]:
    """
    Ping expected BGP neighbors from each router.

    router_ips supports single or multiple targets.
    expected_neighbors can use router label or router host as key.
    """
    results = []
    expected_neighbors = expected_neighbors or {}

    for name, host in _resolve_router_targets(router_ips):
        conn = None
        try:
            conn = ConnectHandler(**_build_router(host, device_type))
            neighbors = expected_neighbors.get(name) or expected_neighbors.get(host) or []
            ping_results = []
            for neighbor_ip in neighbors:
                ping_output = conn.send_command(f"ping {neighbor_ip} repeat 3 timeout 1")
                ping_results.append(
                    {
                        "neighbor_ip": neighbor_ip,
                        "output": ping_output,
                    }
                )

            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "ok",
                    "ping_results": ping_results,
                }
            )
        except Exception as e:
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "error",
                    "error": str(e),
                }
            )
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass

    return results


@mcp.tool()
def collect_bgp_incident_bundle(
    router_ips: str | list[str] | None = None,
    device_type: str = "cisco_ios",
) -> list[dict]:
    """
    Collect one-call BGP troubleshooting bundle.

    router_ips supports single or multiple targets.
    """
    results = []

    for name, host in _resolve_router_targets(router_ips):
        conn = None
        try:
            conn = ConnectHandler(**_build_router(host, device_type))
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "ok",
                    "show_clock": conn.send_command("show clock"),
                    "bgp_summary": conn.send_command("show ip bgp summary"),
                    "bgp_neighbors": conn.send_command("show ip bgp neighbors"),
                    "bgp_table": conn.send_command("show ip bgp"),
                    "ip_route": conn.send_command("show ip route"),
                    "bgp_config": conn.send_command("show run | section router bgp"),
                    "bgp_logs": conn.send_command("show logging | include BGP|%BGP"),
                }
            )
        except Exception as e:
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "error",
                    "error": str(e),
                }
            )
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass

    return results


@mcp.tool()
def show_bgp_community(
    router_ip: str,
    community: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show all BGP prefixes tagged with a specific community value on one router.

    community: standard community in AA:NN format (e.g. "65000:100"),
               or well-known value (e.g. "no-export", "no-advertise", "internet").
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        output = conn.send_command(f"show ip bgp community {community}")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "community": community,
            "bgp_community_routes": output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def show_bgp_community_list(
    router_ip: str,
    community_list: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show BGP routes matching a named or numbered community-list on one router.

    community_list: name or number of the community-list (e.g. "10" or "MY_COMM_LIST").
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        output = conn.send_command(f"show ip bgp community-list {community_list}")
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "community_list": community_list,
            "bgp_community_list_routes": output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def show_bgp_prefix_communities(
    router_ip: str,
    prefix: str,
    device_type: str = "cisco_ios",
) -> dict:
    """
    Show communities attached to a specific BGP prefix on one router.
    Uses "show ip bgp <prefix>" and highlights the Community field.
    """
    label, host = _resolve_router_target(router_ip)
    conn = ConnectHandler(**_build_router(host, device_type))
    try:
        output = conn.send_command(f"show ip bgp {prefix}")
        community_line = ""
        for line in output.splitlines():
            if "Community" in line:
                community_line = line.strip()
                break
        return {
            "router": label,
            "host": host,
            "status": "ok",
            "prefix": prefix,
            "community": community_line if community_line else "none",
            "full_bgp_output": output,
        }
    finally:
        conn.disconnect()


@mcp.tool()
def validate_bgp_community_config(
    router_ips: str | list[str] | None = None,
    expected_send_community_neighbors: dict[str, list[str]] | None = None,
    device_type: str = "cisco_ios",
) -> list[dict]:
    """
    Audit BGP community configuration on one or multiple routers.

    Checks:
    - 'neighbor <ip> send-community' is configured per eBGP peer
      (communities are stripped by default on eBGP sessions without this)
    - 'ip community-list' definitions exist
    - 'route-map' entries reference set/match community

    expected_send_community_neighbors: optional per-router list of neighbor IPs
      that must have send-community configured.
      Example: {"192.168.100.100": ["192.168.100.110", "192.168.100.120"]}
    """
    results = []
    expected_send_community_neighbors = expected_send_community_neighbors or {}

    for name, host in _resolve_router_targets(router_ips):
        conn = None
        try:
            conn = ConnectHandler(**_build_router(host, device_type))
            bgp_config = conn.send_command("show run | section router bgp")
            community_lists = conn.send_command("show run | include ip community-list")
            route_maps = conn.send_command("show run | section route-map")

            issues = []
            checks: dict[str, Any] = {
                "send_community_configured": {},
                "community_lists_defined": bool(community_lists.strip()),
                "route_map_community_references": [],
            }

            # Check send-community per expected neighbor
            neighbors_to_check = (
                expected_send_community_neighbors.get(name)
                or expected_send_community_neighbors.get(host)
                or []
            )
            for neighbor_ip in neighbors_to_check:
                has_send_community = (
                    f"neighbor {neighbor_ip} send-community" in bgp_config
                )
                checks["send_community_configured"][neighbor_ip] = has_send_community
                if not has_send_community:
                    issues.append(
                        f"Missing 'neighbor {neighbor_ip} send-community' — "
                        "communities will be stripped on this eBGP session"
                    )

            # Find route-map lines that reference community
            for line in route_maps.splitlines():
                if "community" in line.lower():
                    checks["route_map_community_references"].append(line.strip())

            if not checks["community_lists_defined"]:
                issues.append("No 'ip community-list' definitions found in running config")

            status = "ok" if not issues else "fail"
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": status,
                    "checks": checks,
                    "issues": issues,
                    "bgp_config": bgp_config,
                    "community_lists": community_lists,
                    "route_map_community_lines": checks["route_map_community_references"],
                }
            )
        except Exception as e:
            results.append(
                {
                    "router": name,
                    "host": host,
                    "status": "error",
                    "error": str(e),
                }
            )
        finally:
            if conn:
                try:
                    conn.disconnect()
                except Exception:
                    pass

    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")