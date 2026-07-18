---
name: bgp-troubleshooting
description: "Use when checking Cisco BGP health, neighbor state, missing routes, or basic peering issues."
---

# BGP Troubleshooting Skill

Simple workflow for quick checks.

## When To Use
Use this skill for prompts like:
- "Neighbor not established"
- "Routes missing"

## Required Inputs
- Router IP target(s)
- Neighbor IP (if known)
- Expected behavior (session state or route visibility)

## Steps
1. Collect router targets and expected state from user input.
2. Run `show_bgp_summary_all` for scope.
3. If one neighbor is impacted, run `show_bgp_neighbor_detail`.
4. If route flow is unclear, run:
- `show_bgp_advertised_routes`
- `show_bgp_received_routes`
5. If needed, run `check_bgp_reachability_matrix` with explicit expected neighbors.

## Keep It Simple
- Prefer read-only checks.
- Report assumptions clearly.
- Return: scope, findings, likely cause, next safe check.
