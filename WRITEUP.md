Team Pyrrhic
Secure the Grid - Tennessee Quantum Hackathon 2026 

Step 1 - BB84 Eavesdropper
    Part 1: near-zero qber w/ no eavesdropper (sifted keys match) 
    Part 2: qber w/ and w/out the eavesdropper 
    Part 3: hardware qber (& quantum emulator's, if you ran), your threshold reasoning, & the job IDs
    Part 4: the written physics explanation 
Step 2 - Size up the threat
    Part 1: Shor Demo (factor 15)
        The team ran Shor's period-finding circuit for N = 15 with base 7. The most useful measured phase was 3/4, giving a period of 4. Using that period, gcd(7² − 1, 15) and gcd(7² + 1, 15) recovered the factors 3 and 5 respectively. Working through the steps showed that the quantum computer's only job is finding the period; the rest is ordinary arithmetic. Since RSA's security depends on factoring being hard, and a related method breaks elliptic-curve cryptography, this is the threat to most of the public-key encryption a utility uses today.
    Part 2: How Far is Real Hardware? 
        The largest machine available through qBraid has 107 qubits, Rigetti Cepheus-1-108Q. According to Google Quantum AI Researcher Gidney (2025), it would take approximately 1,400 error-corrected (logical) qubits, built from one million noisy physical qubits, running for under a week to break RSA-2048. For reference, the previous proof of concept of Shor's Algorithm used 8 counting qubits and 4 work qubits for a total of 12. Given Rigetti's max of 107 qubits, the problem would require 9,000 times more physical qubits than currently available, roughly four orders of magnitude. The same author Gidney had made an estimate of 20 million in 2019, thus indicating that despite being real, the gap is shrinking quickly. However, qubit count alone understates the gap present. The estimate does not take into consideration the difficulty of error mitigation. The given estimates assume 0.1% gate error across the entire quantum computer, however, to obtain such an error rate, each logical qubit would need hundreds of physical qubits for error correction. 
    Part 3: Exposure Map
        The utility systems that currently rely on RSA or elliptic-curve cryptography (ECC) include the following: 
          - firmware update signing (RSA/ECDSA) 
          - device certificates (RSA/ECDSA)
          - remote-access VPN (ECDH w/ RSA/ECDSA) 
          - control center links (TLS/IPsec - ECDH/RSA key exchange) 
          - SCADA/DNP3 (ECDH/RSA key exchange) 
          - smart meters (ECDH/ECDSA) 
    Part 4: Migration Plan 
    Part 5: Grover and Symmetric Keys
