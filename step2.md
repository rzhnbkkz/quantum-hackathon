# Step 2 - Size Up the Threat

## Part 1: Shor Demo (Factor 15)

The team ran Shor's period-finding circuit for N = 15 with base 7. The most useful measured phase was 3/4, giving a period of 4. Using that period, gcd(7² − 1, 15) and gcd(7² + 1, 15) recovered the factors 3 and 5 respectively. Working through the steps showed that the quantum computer's only job is finding the period; the rest is ordinary arithmetic. Since RSA's security depends on factoring being hard, and a variant of Shor's algorithm solves the discrete logarithm problem behind elliptic-curve cryptography, this is the threat to most of the public-key encryption a utility uses today.

## Part 2: How Far Is Real Hardware?

The largest machine available through qBraid has 107 qubits, Rigetti Cepheus-1-108Q. For comparison, our factor-15 demo used 8 counting qubits and 4 work qubits for a total of 12. According to Google Quantum AI researcher Gidney (2025), breaking RSA-2048 would take approximately 1,400 error-corrected (logical) qubits, built from just under one million noisy physical qubits, running for under a week. Given Rigetti's max of 107 qubits, the problem would require roughly 9,000 times more physical qubits than currently available, about four orders of magnitude.

In 2019, Gidney and Ekerå estimated 20 million physical qubits for the same task; the 20-fold drop in six years indicates that the gap, while real, is shrinking quickly.

However, qubit count alone understates the gap present. The one million figure already includes the cost of error correction, roughly 700 physical qubits per logical qubit, but it assumes every gate across the entire machine has an error rate of 0.1% or better. Today's devices approach that rate only on small chips, not at the scale of a million qubits. The estimate also assumes the machine runs continuously for days while error correction, including repeated measurement and real-time decoding, keeps pace the entire time.

For reference, error-corrected demonstrations to date have produced at most tens of logical qubits, not 1,400. Thus, the true gap lies in both scale and quality: more qubits, lower error rates across all of them, and sustained error-corrected operation.

References: C. Gidney, "How to factor 2048 bit RSA integers with less than a million noisy qubits," 2025. C. Gidney and M. Ekerå, "How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits," 2019.

## Part 3: Exposure Map

The utility systems that currently rely on RSA or elliptic-curve cryptography (ECC) include the following, along with how long each must remain secure:

| System | Cryptography | Threat | Service life |
|---|---|---|---|
| firmware update signing | RSA/ECDSA | forged updates | 15–30 years |
| device certificates | RSA/ECDSA | impersonation | 10+ years |
| remote-access VPN | ECDH w/ RSA/ECDSA | harvest now, decrypt later (HNDL) | 5–10 years |
| control center links | TLS/IPsec - ECDH/RSA key exchange | decryption and forgery | 10+ years |
| SCADA/DNP3 | ECDH/RSA key exchange | HNDL | 15–30 years |
| smart meters | ECDH/ECDSA | HNDL | 15–20 years |

## Part 4: Migration Plan

The migration follows NIST IR 8547 (finalized October 27, 2026), which deprecates all quantum-vulnerable public-key algorithms after 2030 and disallows them after 2035. Systems are ranked by how exposed they are today and how long they take to fix, with an inventory of every RSA and ECC system running alongside the first fixes rather than delaying them.

1. Firmware signing comes first because it has the longest lead time: a forged update could control a device for its entire service life, and devices shipping today must already carry a post-quantum verification key. It moves to hash-based signatures, either stateful LMS/XMSS (SP 800-208) or stateless SLH-DSA (FIPS 205), along with the PKI root that every device certificate chains back to.
2. In parallel, remote-access VPNs and device certificates, the most likely HNDL targets, move to ML-KEM (FIPS 203) and ML-DSA (FIPS 204) in hybrid mode with existing ECC.
3. Control center links and SCADA follow before 2030, with add-on gateways for older RTUs.
4. Last, symmetric encryption moves to AES-256 for new long-lived links, a simple configuration change (see [Part 5](step2b.md)).

## Stretch

Field devices stay in service for 20 to 30 years, so a device installed today will still be running past NIST's 2035 disallowance date. By Mosca's inequality, if the time a system must stay secure plus the time to migrate exceeds the time until a quantum computer can break RSA, the utility is already late.

The hardest cases are firmware roots of trust burned into read-only memory, which can never be replaced; older RTUs, such as one running an ARM Cortex-M3 with 128 KB of flash, that lack the resources for post-quantum algorithms; protective relays, which must act within milliseconds while ML-DSA signatures are about 2.4 KB compared to 64 bytes for ECDSA; and smart meters and remote substations, where scale, outage windows, and NERC CIP change management slow every update.

Since these systems cannot simply be patched, the utility should require post-quantum support and crypto-agility in all new equipment purchases, protect legacy devices with gateways, segmentation, and the quantum key distribution demonstrated in Step 1, and schedule replacements alongside existing capital cycles.
