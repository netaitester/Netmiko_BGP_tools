---
name: bgp-route-exchange-issues
description: "Use when BGP is up but routes are not being received or advertised as expected."
---

# BGP Route Exchange Skill

Focused workflow for route advertisement and reception problems.

## When To Use
Use this skill for prompts like:
- "BGP up but no routes"
- "Not receiving routes from neighbor"
- "Not advertising expected prefixes"

## Required Inputs
- Router IP target(s)
- Neighbor pair(s) to inspect
- Expected prefixes or policy intent

## Steps
1. Collect router and neighbor pairs from user input.
2. Run `show_bgp_summary_all` to confirm sessions are established.
3. Run `show_bgp_received_routes` for affected router/neighbor pairs.
4. Run `show_bgp_advertised_routes` for affected router/neighbor pairs.
5. Run `show_bgp_neighbor_detail` to inspect policy/session context.
6. If needed, run `validate_bgp_config_all` with `expected_neighbors`/`expected_networks`.

## Keep It Simple
- Separate "session up" from "route flow broken".
- Compare received vs advertised outputs before concluding policy issues.
- Return: missing direction (in/out), likely policy/config gap, next safe check.
