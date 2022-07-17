.PHONY: clean

CFLAGS ?= -O2 -Wall -Werror -Wpedantic
LDLIBS = -lpng
LDFLAGS = -L/usr/local/opt/argp-standalone/lib/

TARGET = vtf2png 
SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:%.c=%.o)

$(TARGET): $(OBJECTS)

clean:
	$(RM) $(TARGET) $(OBJECTS)
