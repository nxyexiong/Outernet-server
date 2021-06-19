import os


def init_tun():
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    os.system("iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE")
    # fix system udp buffer size
    os.system("sysctl -w net.core.rmem_max=26214400")
    os.system("sysctl -w net.core.rmem_default=26214400")


def uninit_tun():
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")


def install_tun(tun_name, tun_ip, dst_ip):
    os.system("ip tuntap add dev %s mode tun" % (tun_name,))
    os.system("ifconfig %s mtu 1300 up" % (tun_name,))
    os.system("ifconfig %s %s dstaddr %s up" % (tun_name, tun_ip, dst_ip))


def uninstall_tun(tun_name):
    os.system("ip link delete %s" % (tun_name,))
