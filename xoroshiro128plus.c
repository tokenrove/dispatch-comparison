/*  Written in 2016 by David Blackman and Sebastiano Vigna (vigna@acm.org)

To the extent possible under law, the author has dedicated all copyright
and related and neighboring rights to this software to the public domain
worldwide. This software is distributed without any warranty.

See <http://creativecommons.org/publicdomain/zero/1.0/>. */

#include <stdint.h>

uint64_t xorshift_seed[2];

static inline uint64_t rotl(const uint64_t x, int k) {
	return (x << k) | (x >> (64 - k));
}

uint64_t next(void) {
	const uint64_t s0 = xorshift_seed[0];
	uint64_t s1 = xorshift_seed[1];
	const uint64_t result = s0 + s1;

	s1 ^= s0;
	xorshift_seed[0] = rotl(s0, 55) ^ s1 ^ (s1 << 14); // a, b
	xorshift_seed[1] = rotl(s1, 36); // c

	return result;
}
