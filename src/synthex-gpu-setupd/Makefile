# synthex-gpu-setupd Makefile
# GPU detection and driver setup daemon for SynthOS
CC      ?= gcc
CFLAGS  ?= -O2 -Wall -Wextra -Wpedantic -std=c11
LDFLAGS ?=

PREFIX  ?= /usr
BINDIR  ?= $(PREFIX)/bin

TARGET = synthex-gpu-setupd
SRCS   = gpu-detect.c
OBJS   = $(SRCS:.c=.o)

.PHONY: all clean install

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)

install: $(TARGET)
	install -d $(DESTDIR)$(BINDIR)
	install -m 0755 $(TARGET) $(DESTDIR)$(BINDIR)/
	install -d $(DESTDIR)/usr/lib/systemd/system
	install -m 0644 ../../systemd/synthex-gpu-setupd.service $(DESTDIR)/usr/lib/systemd/system/
