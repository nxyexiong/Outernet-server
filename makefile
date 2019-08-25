CC=gcc
CFLAGS=-Wall -g

all:
	$(CC) $(CFLAGS) hello.cpp

clean:
	rm -rf *.o 