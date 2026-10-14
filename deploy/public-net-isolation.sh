#!/bin/sh
# Keep the isolated "public" docker network (nhl-gamecard, cloudflared) away from
# the host and the LAN: containers on it may reach the internet and each other,
# but can't open connections to the host's services, other docker networks
# (including ports published on 192.168.1.235) or any private address.
# Replies to connections made *into* the network (e.g. curl 127.0.0.1:8000) are
# unaffected, since only NEW connections are dropped. Idempotent; run as root.
set -eu

NET=172.30.0.0/24   # must match networks.public subnet in compose.yml

# -C checks whether the rule exists; -I inserts it at the top of the chain.
add() {
  chain=$1; shift
  iptables -C "$chain" "$@" 2>/dev/null || iptables -I "$chain" "$@"
}

# Forwarded traffic (LAN, other docker networks, DNAT'd published ports).
# Inserted in reverse order, so the RETURN for traffic inside the network ends up first.
for dst in 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 100.64.0.0/10; do
  add DOCKER-USER -s "$NET" -d "$dst" -m conntrack --ctstate NEW -j DROP
done
add DOCKER-USER -s "$NET" -d "$NET" -j RETURN

# Traffic to the host itself (natively running services such as Plex and SSH, the gateway IP).
add INPUT -s "$NET" -m conntrack --ctstate NEW -j DROP
