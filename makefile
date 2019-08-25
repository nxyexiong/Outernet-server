CC=gcc
CFLAGS=-Wall -g -Ilwip/src/include -Ilwip/custom

all:
	$(CC) $(CFLAGS) main.cpp -o outernet-server

clean:
	rm -rf *.o 