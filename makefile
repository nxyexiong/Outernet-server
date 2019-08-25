CC=gcc
CFLAGS=-Wall -g

LWIP_INCLUDES:= \
    lwip/src/include/ipv4 \
    lwip/src/include/ipv6 \
    lwip/src/include \
    lwip/custom \

LWIP_SOURCES:= \
	lwip/src/core/udp.c \
    lwip/src/core/memp.c \
    lwip/src/core/init.c \
    lwip/src/core/pbuf.c \
    lwip/src/core/tcp.c \
    lwip/src/core/tcp_out.c \
    lwip/src/core/netif.c \
    lwip/src/core/def.c \
    lwip/src/core/ip.c \
    lwip/src/core/mem.c \
    lwip/src/core/tcp_in.c \
    lwip/src/core/stats.c \
    lwip/src/core/inet_chksum.c \
    lwip/src/core/timeouts.c \
    lwip/src/core/ipv4/icmp.c \
    lwip/src/core/ipv4/igmp.c \
    lwip/src/core/ipv4/ip4_addr.c \
    lwip/src/core/ipv4/ip4_frag.c \
    lwip/src/core/ipv4/ip4.c \
    lwip/src/core/ipv4/autoip.c \
    lwip/src/core/ipv6/ethip6.c \
    lwip/src/core/ipv6/inet6.c \
    lwip/src/core/ipv6/ip6_addr.c \
    lwip/src/core/ipv6/mld6.c \
    lwip/src/core/ipv6/dhcp6.c \
    lwip/src/core/ipv6/icmp6.c \
    lwip/src/core/ipv6/ip6.c \
    lwip/src/core/ipv6/ip6_frag.c \
    lwip/src/core/ipv6/nd6.c \
    lwip/custom/sys.c \

all: $(LWIP_SOURCES) $(LWIP_INCLUDES)
	$(CC) $(CFLAGS) hello.cpp

clean:
	rm -rf *.o 