echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
ip tuntap add dev $1 mode tun
ifconfig $1 $2 dstaddr $3 up