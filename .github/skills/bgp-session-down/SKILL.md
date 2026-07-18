---
name: bgp-session-down
description: "Use when BGP neighbor is down, stuck in Idle/Active, or not establishing on Cisco IOS."
---

# BGP Session Down Skill

Focused workflow for session establishment issues.

## When To Use
Use this skill for prompts like:
- "Neighbor stuck in Idle"
- "BGP not establishing"

## Required Inputs
- Router IP target(s)
- Neighbor IP(s) expected to be up
- Expected peering state (Established, Idle, Active)

## Steps
1. Collect router targets and expected neighbors from user input.
2. Run `show_bgp_summary_all` to identify impacted routers/neighbors.
3. Run `show_bgp_neighbor_detail` for each impacted neighbor.
4. Run `check_bgp_reachability_matrix` to verify L3 reachability to expected neighbors.
5. If issue remains unclear, run `collect_bgp_incident_bundle`.

## Keep It Simple
- Prefer read-only checks.
- Confirm whether issue is control-plane (BGP) or transport/reachability.
- Return: impacted neighbors, state, likely cause, next safe check.
