CC=gcc
CFLAGS=-Wall -g -Ilwip/src/include

all:
	$(CC) $(CFLAGS) main.cpp

clean:
	rm -rf *.o 