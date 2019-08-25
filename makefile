CC=gcc
CFLAGS=-Wall -g -Ilwip/include

LWIPSRC=lwip/core/udp.c \
        lwip/core/memp.c \
        lwip/core/init.c \
        lwip/core/pbuf.c \
        lwip/core/tcp.c \
        lwip/core/tcp_out.c \
        lwip/core/netif.c \
        lwip/core/def.c \
        lwip/core/ip.c \
        lwip/core/mem.c \
        lwip/core/tcp_in.c \
        lwip/core/stats.c \
        lwip/core/inet_chksum.c \
        lwip/core/timeouts.c \
        lwip/core/ipv4/icmp.c \
        lwip/core/ipv4/igmp.c \
        lwip/core/ipv4/ip4_addr.c \
        lwip/core/ipv4/ip4_frag.c \
        lwip/core/ipv4/ip4.c \
        lwip/core/ipv4/autoip.c \
        lwip/core/ipv6/ethip6.c \
        lwip/core/ipv6/inet6.c \
        lwip/core/ipv6/ip6_addr.c \
        lwip/core/ipv6/mld6.c \
        lwip/core/ipv6/dhcp6.c \
        lwip/core/ipv6/icmp6.c \
        lwip/core/ipv6/ip6.c \
        lwip/core/ipv6/ip6_frag.c \
        lwip/core/ipv6/nd6.c \

all: lwip.o main.o
	$(CC) $(CFLAGS) -o outernet-server main.o lwip.o

main.o:
	$(CC) $(CFLAGS) main.cpp

lwip.o:
	$(CC) $(CFLAGS) $(LWIPSRC)

clean:
	rm -rf *.o 