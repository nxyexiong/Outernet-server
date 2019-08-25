CC=gcc
CFLAGS=-Wall -g -Ilwip/src/include -Ilwip/custom

all:
	$(CC) $(CFLAGS) main.cpp

clean:
	rm -rf *.o 