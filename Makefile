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

# Note that you may have to change -DHAVE_GETRANDOM to -DHAVE_RDRAND
# depending on what kernel and hardware you have.
CFLAGS ?= -Wall -pedantic -std=gnu11 -I. -Igenerated -O3 -g -DHAVE_GETRANDOM
LDFLAGS ?= -lm

all: run-experiment
run-experiment: clean generate-files run-trials analyze-results

generated/:
	mkdir -p generated/

%.o: %.c
	$(CC) $(CFLAGS) -DN_ENTRIES=$(N_ENTRIES) -o $@ -c $^

HEADER_FILES := dispatch.h dummy-fns.h
DRIVER_OBJS := main.o generated/dummy-fns.o ns-$(CALL_DISTRIBUTION).o xoroshiro128plus.o
$(PLATFORM)-linear: generated/$(PLATFORM)-linear.o $(DRIVER_OBJS)
$(PLATFORM)-binary: generated/$(PLATFORM)-binary.o $(DRIVER_OBJS)
$(PLATFORM)-vtable: generated/$(PLATFORM)-vtable.o $(DRIVER_OBJS)
c-switch: generated/c-switch.o $(DRIVER_OBJS)
c-vtable: generated/c-vtable.o $(DRIVER_OBJS)

%.c: $(HEADER_FILES)

$(TRIALS):
	$(CC) -static $(CFLAGS) -o $@ $^ $(LDFLAGS)

GENERATED_FILES := generated/dummy-fns.h generated/dummy-fns.c \
	generated/$(PLATFORM)-linear.s generated/$(PLATFORM)-binary.s \
	generated/$(PLATFORM)-vtable.s generated/c-switch.c generated/c-vtable.c

$(GENERATED_FILES): generator

GENERATOR_FLAGS=--fn-work=$(FN_WORK) --fn-alignment=$(FN_ALIGNMENT) --n-entries=$(N_ENTRIES)
generate-files: generated/ generator
	./generator $(GENERATOR_FLAGS) $(GENERATED_FILES)

run-trials: $(shell shuf -e $(TRIALS))
	for i in $^; do \
	  echo running $$i in $(THIS_RUN); \
	  perf stat -r $(N_RUNS) ./$$i $(N_DISPATCHES) ||:; \
	done

clean:
	$(RM) *.o $(GENERATED_FILES) $(TRIALS)
