## Step 2, Part 5

**What Grover means for AES.** Grover speeds up key guessing by a square root (2^128 keys becomes about 2^64 rounds, which is still a lot), but the rounds must run one after another (e.g. N = 16 requires 3 rounds, and round 2 must wait for round 1 to finish). Splitting the work across many machines isn't as effective, either, as Grover's search barely benefits from parallelization unlike regular brute-force attacks. Using M machines only makes it √M times faster, and every round of a real attack is a full AES computation on an error-corrected quantum computer.

**Key length.** Grover will likely give little or no advantage against AES, and that AES-128 will stay secure for decades. NIST IR 8547 keeps all AES key sizes allowed after 2035. We recommend AES-256 for data and links that must stay secret for 10+ years, as a cheap margin of safety rather than an emergency.

**Compared with RSA: less urgent, and easier.** Shor's algorithm computes RSA and elliptic-curve private keys directly, so longer keys don't save them, and "harvest now, decrypt later" puts today's recorded traffic at risk. Fixing that means new algorithms (ML-KEM, ML-DSA), new certificates and firmware updates on field devices. Moving from AES-128 to AES-256 is usually a configuration change on equipment that already supports it. In our migration plan, the RSA and elliptic-curve replacement comes first, and AES-256 rides along with it.

*Sources:* NIST Post-Quantum Cryptography FAQ; NIST IR 8547 (Transition to Post-Quantum Cryptography Standards); F. Valsorda, "Quantum Computers Are Not a Threat to 128-bit Symmetric Keys" (2026), https://words.filippo.io/128-bits/; https://www.encryptionconsulting.com/grovers-algorithm-and-aes-256/

## Run record

| N | Device | Job ID | Shots | Status | Result |
|---|---|---|---|---|---|
| N=4 | IonQ simulator (forte-1 noise model) | ionq:ionq:sim:simulator-0ad7-qjob-6af7e58ef15852ed27b72b26 | 200 | Completed | 200/200 on key (100%) |
| N=8 | IonQ simulator (forte-1 noise model) | ionq:ionq:sim:simulator-0ad7-qjob-6af86a41c8f5265fb3f1b033 | 200 | Completed | 158/200 on key (79%) |
| N=16 | IonQ simulator (forte-1 noise model) | ionq:ionq:sim:simulator-0ad7-qjob-6af7e25ef15852ed27b72a6b | 200 | Completed | 87/200 on key (44%) |
| N=16 | Quantinuum H2 emulator | quantinuum:quantinuum:sim:h2-emulator-0ad7-qjob-6af86c52c8f5265fb3f1b0ee | 200 | Completed | 165/200 on key (82.5%) |

**Note** On the noise-free simulator Grover's Search found the key about 100%, 95% and 97% of the time for N = 4, 8 and 16, respectively. 
On IonQ’s simulator with a Forte noise model, it fell to 100%, 79% and 44% as the circuit grew. On Quantinuum's H2 emulator, N = 16 reached 82.5%. How much noise hurts depends heavily on the machine, but every noisy run lost ground as the search grew.
