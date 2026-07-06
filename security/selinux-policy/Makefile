# Solus SELinux Policy Module Makefile
# Build: make -f /usr/share/selinux/devel/Makefile
# Install: semodule -i solus-policy.pp

TARGET=solus-policy

all: $(TARGET).pp

$(TARGET).pp: $(TARGET).te $(TARGET).fc $(TARGET).if
	make -f /usr/share/selinux/devel/Makefile $(TARGET).pp

install: $(TARGET).pp
	semodule -i $(TARGET).pp
	restorecon -Rv /usr/bin/solus* /etc/solus/

clean:
	rm -f *.pp *.tg *.tmp

check:
	checkpolicy -M -c $(shell grep SELINUX_VERSION /etc/selinux/config 2>/dev/null | cut -d= -f2 || echo 33) -o /dev/null $(TARGET).te

.PHONY: all install clean check
