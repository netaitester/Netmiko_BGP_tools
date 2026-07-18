---
name: bgp-route-missing-prefix
description: "Use when one specific prefix is missing, unstable, or not installed as expected."
---

# BGP Missing Prefix Skill

Focused workflow for single-prefix troubleshooting.

## When To Use
Use this skill for prompts like:
- "Prefix X is missing"
- "Specific route not in BGP"
- "Route seen on one router but not another"

## Required Inputs
- Prefix (CIDR)
- Source router IP and destination router IP
- Neighbor IP(s) in the path (if known)

## Steps
1. Collect prefix and impacted routers from user input.
2. Run `show_bgp_routes_prefix` on the source and destination routers for the same prefix.
3. Run `show_bgp_received_routes` on the receiver-side neighbor to verify inbound visibility.
4. Run `show_bgp_advertised_routes` on the sender-side neighbor to verify outbound advertisement.
5. Run `show_ip_route` on the affected router to verify RIB installation.
6. If needed, run `validate_bgp_config_all` with `expected_networks` for the prefix.

## Keep It Simple
- Track one prefix end-to-end across peers.
- Confirm whether failure is advertise, receive, or install.
- Return: where the prefix disappears, likely cause, next safe check.
