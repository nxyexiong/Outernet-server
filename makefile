CC=gcc
CFLAGS=-Wall -g -Ilwip/includes

all:
	$(CC) $(CFLAGS) main.cpp

clean:
	rm -rf *.o 