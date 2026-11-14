Step 2 - Size up the threat
    Part 1: Shor Demo (factor 15)
        The team ran Shor's period-finding circuit for N = 15 with base 7. The most useful measured phase was 3/4, giving a period of 4. Using that period, gcd(7² − 1, 15) and gcd(7² + 1, 15) recovered the factors 3 and 5 respectively. Working through the steps showed that the quantum computer's only job is finding the period; the rest is ordinary arithmetic. Since RSA's security depends on factoring being hard, and a related method breaks elliptic-curve cryptography, this is the threat to most of the public-key encryption a utility uses today.
    Part 2: How Far is Real Hardware? 
        The largest machine available through qBraid has 107 qubits, Rigetti Cepheus-1-108Q. According to Google Quantum AI Researcher Gidney (2025), it would take approximately 1,400 error-corrected (logical) qubits, built from one million noisy physical qubits, running for under a week to break RSA-2048. For reference, the previous proof of concept of Shor's Algorithm used 8 counting qubits and 4 work qubits for a total of 12. Given Rigetti's max of 107 qubits, the problem would require 9,000 times more physical qubits than currently available, roughly four orders of magnitude. The same author Gidney had made an estimate of 20 million in 2019, thus indicating that despite being real, the gap is shrinking quickly. However, qubit count alone understates the gap present. The estimate does not take into consideration the difficulty of error mitigation. The given estimates assume 0.1% gate error across the entire quantum computer, however, to obtain such an error rate, each logical qubit would need hundreds of physical qubits for error correction. 
    Part 3: Exposure Map
        The utility systems that currently rely on RSA or elliptic-curve cryptography (ECC) include the following: 
          - firmware update signing (RSA/ECDSA)
              + threat: forged updates -> service life 15-30 years
          - device certificates (RSA/ECDSA)
              + threat: impersonation -> service life 10+ years
          - remote-access VPN (ECDH w/ RSA/ECDSA) 
              + threat: HDNL -> service life 5-10 years
          - control center links (TLS/IPsec - ECDH/RSA key exchange) 
              + threat: decryption and forgery -> service life 10+ years
          - SCADA/DNP3 (ECDH/RSA key exchange) 
              + threat: HDNL -> service life 15-30 years 
          - smart meters (ECDH/ECDSA) 
              + threat: HDNL -> service life 15-20 years
    Part 4: Migration Plan
        Before any migration plans can begin, it is necessary to identify the vulnerable systems. Thus, the first step is an inventory of every system using RSA or elliptic-curve cryptography. The exposure map above illustrates forged updates could control a device for its entire service life, thus its crucial to prevent those forged updates outright. This can be done by moving firmware update signing to hash-based signatures (eg. SP 800-208, FIPS 205), whose security depends only on hash functions. The next objective would be to move remote-access VPNs and device certificates to ML-KEM (FIPS 203) for key exchange and ML-DSA (FIPS 204) for signatures. Since the aforementioned are the most likely to be targets of HDNL, it is crucial to commit these changes immediately. The next step would be to integrate the same post-quantum protection on control centers and substations, with add-on gateways for older RTUs that cannot run the new algorithms. The last step is symmetric encryption. The following section on Grover's search exemplifies the benefits of a simple configuration upgrade for new long-lived links to AES-256. 
