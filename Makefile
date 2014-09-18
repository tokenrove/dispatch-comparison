# Experiment scaffold for dispatch-microbenchmarks blog post
# Julian Squires <julian@cipht.net> / 2014
#
# Run make help for tuning information.

.PHONY: help all clean mrproper run-experiment clean-old-results build-trials \
  run-trials analyze-results

PLATFORM ?= $(shell uname -m)
FN_ALIGNMENT ?= default
FN_WORK ?= none
N_ENTRIES ?= 10
N_DISPATCHES ?= 4200
N_RUNS ?= 10
CALL_DISTRIBUTION ?= sequential
FACTORS ?= strategy alignment distribution flush

TRIALS := c-switch c-vtable $(PLATFORM)-linear $(PLATFORM)-binary $(PLATFORM)-vtable

help:
	@echo Usage: make run-experiment
	@echo
	@echo Tunable parameters:
	@echo "  FN_ALIGNMENT"
	@echo "  FN_WORK={none,clflush,memcpy}"
	@echo "  CALL_DISTRIBUTION={sequential,constant,uniform,pareto}"
	@echo "  N_ENTRIES"
	@echo "  N_DISPATCHES"
	@echo "  N_RUNS"
	@echo
	@echo The following trials will be run:
	@echo "  $(TRIALS)"

THIS_RUN := results-$(shell date +%Y%m%d-%H%M%S)

CFLAGS ?= -Wall -pedantic -std=gnu11 -O3 -g
LDFLAGS ?= -lm

all: run-experiment
run-experiment: clean-old-results generate-files run-trials analyze-results
	mkdir $(shell hostname)-$(shell date +%y%m%d)

%.o: %.c
	$(CC) $(CFLAGS) -DN_ENTRIES=$(N_ENTRIES) -o $@ -c $^

HEADER_FILES := dispatch.h dummy-fns.h
DRIVER_OBJS := main.o dummy-fns.o ns-$(CALL_DISTRIBUTION).o
$(PLATFORM)-linear: $(PLATFORM)-linear.o $(DRIVER_OBJS)
$(PLATFORM)-binary: $(PLATFORM)-binary.o $(DRIVER_OBJS)
$(PLATFORM)-vtable: $(PLATFORM)-vtable.o $(DRIVER_OBJS)
c-switch: c-switch.o $(DRIVER_OBJS)
c-vtable: c-vtable.o $(DRIVER_OBJS)

%.c: $(HEADER_FILES)

$(TRIALS):
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

GENERATED_FILES := dummy-fns.h dummy-fns.c $(PLATFORM)-linear.s $(PLATFORM)-binary.s $(PLATFORM)-vtable.s c-switch.c c-vtable.c

$(GENERATED_FILES): generator

GENERATOR_FLAGS=--fn-work=$(FN_WORK) --fn-alignment=$(FN_ALIGNMENT) --n-entries=$(N_ENTRIES)
generate-files: generator
	./generator $(GENERATOR_FLAGS) $(GENERATED_FILES)

run-trials: $(shell shuf -e $(TRIALS))
	for i in $^; do \
	  echo running $$i in $(THIS_RUN); \
	done

clean:
	$(RM) *.o $(GENERATED_FILES) $(TRIALS)
