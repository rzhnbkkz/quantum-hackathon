# Secure the Grid: WRITEUP

Track: UTC Secure the Grid. Each answer is labeled by step and Part. The run record for every cloud run is at the end.

# Step 1: Catch the Eavesdropper (BB84)

## Step 1, Part 1: BB84 and Eavesdropper Detection

The team built a BB84 simulation to show how two people can create a shared secret key and check whether someone may have intercepted the qubits. Alice generates random bits and randomly chooses a basis for each one. She encodes each bit as a qubit and sends it to Bob. Bob independently chooses a random basis to measure each qubit. Afterward, Alice and Bob compare their basis choices over a public channel and keep only the bits where they used the same basis. These remaining bits are called the sifted key.

The team tested an intercept-and-resend eavesdropper. Eve measures each qubit in a randomly chosen basis, then prepares a new qubit based on her result and sends it to Bob. If Eve chooses the wrong basis, her measurement can change the state. Alice and Bob estimate the quantum bit error rate (QBER) by comparing their sifted bits.

## Step 1, Part 2: Results

With no eavesdropper, the local simulator produced a QBER of 0.0. With Eve intercepting and resending the qubits, the QBER was 0.243, or about 24%. This is close to the expected error rate of about 25% for this attack: Eve chooses the wrong basis about half the time, and those wrong-basis measurements cause errors in about half of the affected sifted bits. The exact result can vary between runs because the bits, bases, and measurements are random.

The team also tested a batched circuit with 16 qubits and 200 shots. The local simulator gave a QBER of 0.0. The IonQ simulator run gave a QBER of 0.001. Its job ID was `ionq:ionq:sim:simulator-b095-qjob-6af88876c8f5265fb3f1bd01`.

The team then ran the batched circuit on the IonQ Forte 1 quantum processor through Open Quantum, using 200 shots. The hardware QBER was 0.004, or about 0.4%. Its job ID was `openquantum:ionq:qpu:forte-1-b095-qjob-6af88c54c8f5265fb3f1bdde`. This hardware run did not include Eve; the Eve result came from the local simulator.

## Step 1, Part 3: What the Result Shows

The comparison shows how an intercept-and-resend attack can raise the error rate in the sifted key. A higher QBER can warn Alice and Bob that the communication may have been disturbed. It does not identify who caused the errors: noise, transmission problems, or device errors could also raise QBER. A QBER of 0.0 in one run does not prove that nobody intercepted the qubits.

For this demonstration, a QBER around 10% or higher would be a useful warning threshold. It is well above the 0.4% hardware baseline from this run and below the roughly 25% expected from the simulated intercept-and-resend attack. This is only an illustrative threshold for these tests, not a setting for a real QKD system. The threshold for a deployed system would need to account for its measured noise, sample size, and security requirements.

The team also tested a spy who only intercepts some of the qubits (the sweep cell in the notebook). The expected error rate is about one quarter of the fraction Eve intercepts. If Eve intercepts only 2% of the qubits, the expected QBER is about 0.5%, which is close to the 0.4% the hardware showed with no spy at all. So a careful spy who only listens to a few qubits could hide inside normal noise.

Real QKD systems handle this by assuming every error was caused by a spy. They fix the errors with error correction and then use privacy amplification, which shrinks the key until the spy knows almost nothing about what is left. The more errors there are, the more the key shrinks. Above about 11% QBER, BB84 cannot produce a secure key at all and the key is thrown away (Shor and Preskill, 2000).

## Step 1, Part 4: Physics

BB84's secrecy comes from physics, as measuring a qubit in the wrong basis gives a random result and changes the qubit, and Eve does not know which basis Alice used. She also cannot copy the qubit and measure the copy later because the no-cloning theorem says an unknown quantum state cannot be copied. So any information Eve gains causes errors, which is the jump to about 25% QBER in Part 2. Classical key exchange such as RSA or ECDH cannot match this. Anyone on the line can copy its messages perfectly without leaving a trace, and its safety depends on a math problem that Shor's algorithm breaks (Step 2). That is what makes "harvest now, decrypt later" possible. BB84's security does not depend on the attacker's computing power, so a future quantum computer does not help.

BB84 still needs classical cryptography. In a real deployment, Alice and Bob would need to authenticate their public discussion. Without it, Eve could pretend to be Bob to Alice and Alice to Bob, run a separate BB84 session with each, and neither would see any errors. They would also need error correction and privacy amplification before using the remaining bits as a key. BB84 does not encrypt grid traffic by itself: the resulting key would still need to be used by ordinary encryption equipment.

Real QKD systems have been attacked through their hardware and not through the math. In 2010, researchers showed that the detectors in two commercial QKD systems could be controlled with bright light, which let an attacker learn the key without causing errors (Lydersen et al., 2010). For these and other reasons, the NSA and the UK NCSC do not recommend QKD for government use and recommend post-quantum cryptography instead.

Sources:

- P. Shor and J. Preskill, "Simple Proof of Security of the BB84 Quantum Key Distribution Protocol," 2000. https://arxiv.org/abs/quant-ph/0003004
- L. Lydersen et al., "Hacking commercial quantum cryptography systems by tailored bright illumination," 2010. https://arxiv.org/abs/1008.4593
- NSA, "Quantum Key Distribution (QKD) and Quantum Cryptography (QC)." https://www.nsa.gov/Cybersecurity/Quantum-Key-Distribution-QKD-and-Quantum-Cryptography-QC/
- UK NCSC, "Quantum networking technologies." https://www.ncsc.gov.uk/paper/quantum-networking-technologies

## Step 1, Results Table

| Run | Device | Job ID | Shots | Status | Result |
|---|---|---|---|---|---|
| No eavesdropper | Aer local simulator | none (local run) | 200 qubits, 1 shot each | Completed | QBER 0.0 |
| With eavesdropper | Aer local simulator | none (local run) | 200 qubits, 1 shot each | Completed | QBER 0.243 |
| Batched, 16 rounds | Aer local simulator | none (local run) | 200 | Completed | QBER 0.0 |
| Batched, 16 rounds | IonQ simulator | ionq:ionq:sim:simulator-b095-qjob-6af88876c8f5265fb3f1bd01 | 200 | Completed | QBER 0.001 |
| Batched, 16 rounds | IonQ Forte 1 QPU (Open Quantum) | openquantum:ionq:qpu:forte-1-b095-qjob-6af88c54c8f5265fb3f1bdde | 200 | Completed | QBER 0.004 |

**Note** The local simulator has no noise, so it shows 0.0 with no eavesdropper. The IonQ simulator and the real IonQ Forte machine both stayed under 0.5%. With the eavesdropper the error rate jumped to about 24%, which is far above anything the noise caused.

# Step 2: Size Up the Threat

## Step 2, Part 1: Shor Demo (Factor 15)

The team ran Shor's period-finding circuit for N = 15 with base 7. The most useful measured phase was 3/4, giving a period of 4. Using that period, gcd(7² − 1, 15) and gcd(7² + 1, 15) recovered the factors 3 and 5 respectively. Working through the steps showed that the quantum computer's only job is finding the period; the rest is ordinary arithmetic. Since RSA's security depends on factoring being hard, and a variant of Shor's algorithm solves the discrete logarithm problem behind elliptic-curve cryptography, this is the threat to most of the public-key encryption a utility uses today.

## Step 2, Part 2: How Far Is Real Hardware?

The largest machine available through qBraid has 107 qubits, Rigetti Cepheus-1-108Q. For comparison, our factor-15 demo used 8 counting qubits and 4 work qubits for a total of 12. According to Google Quantum AI researcher Gidney (2025), breaking RSA-2048 would take approximately 1,400 error-corrected (logical) qubits, built from just under one million noisy physical qubits, running for under a week. Given Rigetti's max of 107 qubits, the problem would require roughly 9,000 times more physical qubits than currently available, about four orders of magnitude.

In 2019, Gidney and Ekerå estimated 20 million physical qubits for the same task; the 20-fold drop in six years indicates that the gap, while real, is shrinking quickly.

However, qubit count alone understates the gap present. The one million figure already includes the cost of error correction, roughly 700 physical qubits per logical qubit, but it assumes every gate across the entire machine has an error rate of 0.1% or better. Today's devices approach that rate only on small chips, not at the scale of a million qubits. The estimate also assumes the machine runs continuously for days while error correction, including repeated measurement and real-time decoding, keeps pace the entire time.

For reference, error-corrected demonstrations to date have produced at most tens of logical qubits, not 1,400. Thus, the true gap lies in both scale and quality: more qubits, lower error rates across all of them, and sustained error-corrected operation.

References: C. Gidney, "How to factor 2048 bit RSA integers with less than a million noisy qubits," 2025. C. Gidney and M. Ekerå, "How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits," 2019.

## Step 2, Part 3: Exposure Map

The utility systems that currently rely on RSA or elliptic-curve cryptography (ECC) include the following, along with how long each must remain secure:

| System | Cryptography | Threat | Service life |
|---|---|---|---|
| firmware update signing | RSA/ECDSA | forged updates | 15–30 years |
| device certificates | RSA/ECDSA | impersonation | 10+ years |
| remote-access VPN | ECDH w/ RSA/ECDSA | harvest now, decrypt later (HNDL) | 5–10 years |
| control center links | TLS/IPsec - ECDH/RSA key exchange | decryption and forgery | 10+ years |
| SCADA/DNP3 | ECDH/RSA key exchange | HNDL | 15–30 years |
| smart meters | ECDH/ECDSA | HNDL | 15–20 years |

## Step 2, Part 4: Migration Plan

The migration follows NIST IR 8547 (finalized October 27, 2026), which deprecates all quantum-vulnerable public-key algorithms after 2030 and disallows them after 2035. Systems are ranked by how exposed they are today and how long they take to fix, with an inventory of every RSA and ECC system running alongside the first fixes rather than delaying them.

1. Firmware signing comes first because it has the longest lead time: a forged update could control a device for its entire service life, and devices shipping today must already carry a post-quantum verification key. It moves to hash-based signatures, either stateful LMS/XMSS (SP 800-208) or stateless SLH-DSA (FIPS 205), along with the PKI root that every device certificate chains back to.
2. In parallel, remote-access VPNs and device certificates, the most likely HNDL targets, move to ML-KEM (FIPS 203) and ML-DSA (FIPS 204) in hybrid mode with existing ECC.
3. Control center links and SCADA follow before 2030, with add-on gateways for older RTUs.
4. Last, symmetric encryption moves to AES-256 for new long-lived links, a simple configuration change (see [Part 5](#step-2-part-5-grover-and-symmetric-keys)).

## Step 2, Stretch

Field devices stay in service for 20 to 30 years, so a device installed today will still be running past NIST's 2035 disallowance date. By Mosca's inequality, if the time a system must stay secure plus the time to migrate exceeds the time until a quantum computer can break RSA, the utility is already late.

The hardest cases are firmware roots of trust burned into read-only memory, which can never be replaced; older RTUs, such as one running an ARM Cortex-M3 with 128 KB of flash, that lack the resources for post-quantum algorithms; protective relays, which must act within milliseconds while ML-DSA signatures are about 2.4 KB compared to 64 bytes for ECDSA; and smart meters and remote substations, where scale, outage windows, and NERC CIP change management slow every update.

Since these systems cannot simply be patched, the utility should require post-quantum support and crypto-agility in all new equipment purchases, protect legacy devices with gateways, segmentation, and the quantum key distribution demonstrated in Step 1, and schedule replacements alongside existing capital cycles.

## Step 2, Part 5: Grover and Symmetric Keys

**What Grover means for AES.** Grover speeds up key guessing by a square root (2^128 keys becomes about 2^64 rounds, which is still a lot), but the rounds must run one after another (e.g. N = 16 requires 3 rounds, and round 2 must wait for round 1 to finish). Splitting the work across many machines isn't as effective, either, as Grover's search barely benefits from parallelization unlike regular brute-force attacks. Using M machines only makes it √M times faster, and every round of a real attack is a full AES computation on an error-corrected quantum computer.

**Key length.** Grover will likely give little or no advantage against AES, and that AES-128 will stay secure for decades. NIST IR 8547 keeps all AES key sizes allowed after 2035. We recommend AES-256 for data and links that must stay secret for 10+ years, as a cheap margin of safety rather than an emergency.

**Compared with RSA: less urgent, and easier.** Shor's algorithm computes RSA and elliptic-curve private keys directly, so longer keys don't save them, and "harvest now, decrypt later" puts today's recorded traffic at risk. Fixing that means new algorithms (ML-KEM, ML-DSA), new certificates and firmware updates on field devices. Moving from AES-128 to AES-256 is usually a configuration change on equipment that already supports it. In our migration plan, the RSA and elliptic-curve replacement comes first, and AES-256 rides along with it.

*Sources:* NIST Post-Quantum Cryptography FAQ; NIST IR 8547 (Transition to Post-Quantum Cryptography Standards); F. Valsorda, "Quantum Computers Are Not a Threat to 128-bit Symmetric Keys" (2026), https://words.filippo.io/128-bits/; https://www.encryptionconsulting.com/grovers-algorithm-and-aes-256/

**Results.** On the noise-free simulator Grover's Search found the key about 100%, 95% and 97% of the time for N = 4, 8 and 16, respectively. 
On IonQ’s simulator with a Forte noise model, it fell to 100%, 79% and 44% as the circuit grew. On Quantinuum's H2 emulator, N = 16 reached 82.5%. How much noise hurts depends heavily on the machine, but every noisy run lost ground as the search grew.

# Step 3: Design the Network

## Step 3, Part 1: Architecture

A real utility's network layout is restricted information, so we did not use EPB's real network. We used the Texas A&M ACTIVSg70k synthetic grid. It is made up, but it was built to match real U.S. grids and it sits on real towns. We kept every Chattanooga substation plus its direct neighbors, which gives 49 substations and 65 links. The design went through three versions: `3b_network_design.ipynb` (version 0), `3c_network_design_v1.ipynb` (version 1) and the final one in `network_design/final_design.py`, which writes `network_design/final_design.json`.

![Final network design](network_diagram.png)

Orange links carry QKD and PQC. Blue links are PQC only, and dashed blue links are too long for QKD. Dashed green links are new backup routes. Orange squares are trusted nodes.

| What | Number |
|---|---|
| Substations | 49 |
| Links | 65 |
| Link length | 2.1 km shortest, 6.8 km median, 83.1 km longest |
| Links short enough for QKD | 58 of 65 |
| Control centers | 2 (CHATTANOOGA 3 and CHATTANOOGA 11) |
| Links with PQC | all 65 |
| Links with QKD | 8 |
| Trusted nodes | 4 |
| Load with QKD on every hop to a control center | 316.7 of 1,406.4 MW |
| New backup routes | 4 |

We put post-quantum cryptography (PQC) on every link. It works on the equipment and fiber the utility already has, so it covers all 49 substations no matter how long the link is. We would use ML-KEM (FIPS 203) for exchanging keys and ML-DSA (FIPS 204) for signatures, running next to the encryption used today, as in our Step 2 plan.

QKD only goes on a few links, and an optimizer picks them. Each substation gets a score: the load it carries, times the chance its traffic gets tapped, times the chance the BB84 alarm catches the tap. The score drops a little for every trusted node the key passes through. The link between the two control centers counts as the whole system's load, because it carries data about everything. The final version also gives credit for catching taps on the busiest fiber. The optimizer is an integer program. It finds the best set of links for the budget.

With a budget of 8 QKD links and no more than 4 trusted nodes, it picked these links:

- CHATTANOOGA 3 to CHATTANOOGA 24 (3.7 km), CHATTANOOGA 24 to CHATTANOOGA 12 (10 km) and CHATTANOOGA 12 to CHATTANOOGA 11 (4.9 km). These 3 links join the two control centers.
- CHATTANOOGA 11 to CHATTANOOGA 27 (6.6 km), CHATTANOOGA 27 to CHATTANOOGA 21 (3.1 km) and CHATTANOOGA 21 to CHATTANOOGA 23 (13.6 km).
- CHATTANOOGA 3 to ROSSVILLE 2 (14 km).
- CHATTANOOGA 3 to CHATTANOOGA 13 (16 km).

That puts 8 substations behind QKD on every hop to a control center. Together they carry 316.7 MW, which is 22.5% of the 1,406.4 MW on this grid.

Version 1 in `3c` only scored secrecy. At the same budget it picked 7 links and reached 83% of the most risk reduction possible. The budget numbers in Parts 4 and 5 come from that version.

Distance: we assumed a fiber loss of 0.35 dB/km, which is what was measured on EPB's fiber, and that a link can carry QKD if its loss is 10 dB or less. That is about 28.6 km. 7 of the 65 links are longer than that, so they get PQC only.

Number of substations: QKD works between two points, so on a small budget it cannot reach 49 substations. PQC can. That is why QKD is only on 8 links.

Trusted nodes: when a key passes through a substation in the middle, it is unlocked and locked again there, so that substation has to be trusted. Our design has 4 of them: CHATTANOOGA 12, CHATTANOOGA 21, CHATTANOOGA 24 and CHATTANOOGA 27. Every QKD chain is 3 hops or less, which is the length EPB tested.

Timing: the two ends of a QKD link have to agree on time so they can match what was sent with what was received. QKD does not give the substations their time. The utility would keep using the clocks it already has.

Backup routes: 11 substations had only one path to a control center, so a single fiber cut could cut them off. The worst cut would drop 76.8 MW. The design adds 4 backup routes with PQC: SIGNAL MOUNTAIN 1 to JASPER 18 (74.3 km), LA FAYETTE 4 to CLEVELAND 16 (52.3 km), OLD FORT 2 to JASPER 16 (109 km) and CHATTANOOGA 4 to SIGNAL MOUNTAIN 2 (15.5 km). That is 251.1 km in total. After that, no single cut isolates a substation. These routes are proposed and the lengths are estimates. We have not checked that fiber exists along them.

## Step 3, Part 2: Assumptions and Tradeoffs

- The grid is synthetic. It is not EPB's real network.
- We assumed the fiber follows the power lines. Link lengths are estimated from each line's electrical values. They are not measured.
- Fiber loss is assumed to be 0.35 dB/km and the QKD limit 10 dB. Real fiber would have to be measured before buying QKD equipment.
- The grid model does not say where the control centers are. The highest-voltage, most central Chattanooga substation stands in for the main one (CHATTANOOGA 3), and the most central substation within 3 hops stands in for the backup (CHATTANOOGA 11).
- The chance of a tap, the chance the alarm catches it, and the risk at a trusted node are our guesses. To see if the guesses decide the answer, the version 1 optimizer was run 400 times with different values. 4 links were picked every time, and all 4 are in the final design.
- Line noise on a link is assumed to be 2.5%. EPB measured 1.4% to 3.9%.
- PQC is cheap, but it depends on math problems that we believe are hard. QKD depends on physics, but it needs special hardware, spare fiber and trained staff.
- QKD still needs normal authentication, so it does not replace PQC.

Numbers from the EPB field test (Evans et al., 2021): the test network was about 22 km long and had three QKD links of 3.4 km, 10.2 km and 8.3 km. The fiber loss on those links was 1.3 dB, 3.1 dB and 2.9 dB. Two of the links made secret key at about 1,310 and 1,892 bits per second, with error rates of 3.9% and 1.4%. After the keys were relayed through the trusted nodes, the whole network produced 115 bits per second, which is about one 256-bit key every two seconds. The test ran for 28 hours.

Most of our links are in the same range as those links: the median is 6.8 km. A key rate like that is enough to keep refreshing encryption keys. It is not enough to encrypt all the traffic with QKD key directly.

Sources:

- Evans et al., "Trusted Node QKD at an Electrical Utility," IEEE Access, 2021. https://arxiv.org/abs/2103.09877
- Birchfield et al., IEEE Transactions on Power Systems, 2017 (the ACTIVSg70k synthetic grid, from MATPOWER's copy of the case).

## Step 3, Part 3: Working Prototype

We built both options.

**Teleportation link (Option B).** We built the teleportation circuit in `3_secure_grid_link.ipynb`.

The circuit sends the state of qubit 0 to qubit 2. First we entangle qubits 1 and 2. Then Alice links her message qubit to her half of the pair, and Bob's qubit gets two corrections. To check it, we undo the state on qubit 2 at the end. If the link works, qubit 2 reads 0 every time.

On the local simulator, qubit 2 read 0 on 1,024 of 1,024 shots. On the IonQ simulator with noise, it read 0 on 195 of 200 shots. The job ID was `ionq:ionq:sim:simulator-b095-qjob-6af89604c8f5265fb3f1cbf3`.

These are simulator results. We did not run this on real hardware. All three qubits are on one chip, so it shows the logic works but not that it works over a distance.

This could help with the trusted node problem. In QKD, every stop in the middle has to unlock the key and lock it again, so every stop has to be trusted. With teleportation, a middle stop only passes entanglement along and never holds the key. That needs quantum repeaters, which utilities cannot buy yet, so our design keeps QKD chains to 3 hops and treats every middle stop as a trusted node.

**BB84 as a link in the design (Option A).** In `3a_bb84_grid_link.ipynb` we ran BB84 as one link from the design: the 3.7 km link from control center CHATTANOOGA 3 to CHATTANOOGA 24. With 2.5% line noise the quiet link had a QBER of 0.025, so the alarm is set at 0.034. A full tap raised the QBER to 0.269. The alarm caught a tap on 15% of the rounds 98% of the time, but a tap on 5% of the rounds only 63% of the time. So a small tap can still hide.

Through qBraid, the quiet link gave a QBER of 0.000 on the qBraid QIR simulator and on the IonQ simulator. The fully tapped link gave 0.426 and 0.433. Each of those runs is one small batch with about 6 usable rounds, so the result depends on a handful of random choices and came out above the 0.269 average.

**A better alarm.** In `3d_alarm_threshold.ipynb` we tested alarms on line noise that drifts. All three were tuned to about 1 false alarm per 1,000 batches. The table shows how often each one caught the tap.

| Tap size | Fixed threshold | Kalman filter | Kalman + CUSUM |
|---|---|---|---|
| 1% of rounds | 6% | 28% | 50% |
| 2% of rounds | 7% | 32% | 65% |
| 5% of rounds | 20% | 95% | 100% |

Wind gusts on the fiber still fooled every alarm that only looks at QBER. Adding a normal fiber monitor as a second signal raised the catch rate for a 2% tap from 56% to 84%.

**Attacks.** In `3f_attacks_on_hardware.ipynb` we tried five attacks on one BB84 circuit of 12 rounds, so the numbers are rough. Alice's and Bob's random choices came from a 3-shot job on the qBraid QIR simulator. That is a classical simulator, so these bits are not truly random from physics; a real QPU would be needed for that. In a blinding attack, Eve controls Bob's detectors so that he only gets a result when his basis matches hers. We modeled it by keeping only those rounds from the tap run.

On the local simulator with 2.5% line noise, the quiet link had a QBER of 0.019, a full tap 0.207 and a denial of service attack 0.677. The partial tap (3 of 12 rounds) gave 0.024, the same as the line noise: in a circuit this small, the tapped rounds happened to cause no errors. Blinding kept the QBER at 0.021, but only 62% of the rounds gave a result.

On the IonQ Forte 1 quantum computer, the quiet link had a QBER of 0.002, so the alarm was set at 0.009. The full tap gave 0.188 and set off the alarm. Scored as blinding, the same job gave a QBER of 0.002 with only 62% of the rounds giving a result. The error check passed it, and only a click-rate monitor caught it. Each Forte job cost 10 Open Quantum credits, and we ran out after these two, so the partial tap and denial of service jobs were cancelled. We ran them on the IonQ simulator with the Forte noise model instead: the quiet link and the partial tap both gave 0.000, and denial of service gave 0.677.

## Step 3, Part 4: Rollout Plan

1. First: make a list of where the utility uses RSA and elliptic-curve cryptography. Fix firmware signing first, since a fake update would do the most damage. Turn on PQC at the two control centers.
2. Next: add PQC at the other 47 substations. Replace old gateways that cannot be updated.
3. Then, if the budget allows QKD: measure the fiber, and start with the chain that joins the two control centers (CHATTANOOGA 3 to 24 to 12 to 11). In the budget chart in `3c_network_design_v1.ipynb`, the risk reduced jumps from under 10% at a budget of 3 links to about 70% at 4 links, and this chain is the reason. These 3 links and CHATTANOOGA 3 to ROSSVILLE 2 were picked in all 400 test runs of version 1, so they are the safest first purchases.
4. Later: add the other 4 QKD links, and build the 4 backup routes for the 11 substations that have only one path.

## Step 3, Part 5: Cost vs Security

| Option | Cost | What it protects | What is still exposed |
|---|---|---|---|
| Keep what they have | Nothing new | Attackers today | Traffic recorded now can be read later |
| PQC on every link | Software updates and some new gateways | All 65 links | Old devices behind the gateways, fiber cuts |
| PQC + QKD on 8 links + 4 backup routes | Same as above plus 8 QKD links, 4 hardened trusted nodes, about 251 km of backup route, fiber and staff | Adds physics-based keys and tap detection where the risk is highest (316.7 MW behind QKD), and no single fiber cut isolates a substation | Anything a real survey of the fiber turns up |

We recommend PQC on every link first. It protects the whole network for the least money. QKD comes second, starting with the control center chain, and only after the fiber has been measured.

More budget helps less and less. In version 1's budget chart, the first 4 links get to about 70%, 8 links get to 83%, and it takes about 25 links to reach 100%. Where the QKD goes matters more than how much is bought: at the same budget of 8 links, picking the busiest links first reached under 5%. A simple greedy method came within 0.5% of the optimizer, so a careful engineer could get close by hand. The optimizer makes sure of it. The 70%, the 25 links and the 5% are read off the budget chart in `3c_network_design_v1.ipynb`.

We do not have real prices. The budget is counted in QKD links, with a trusted node counted as 0.2 of a link, because QKD vendors do not publish prices. A real comparison would need a quote.

## Step 3, Stretch

We did the QAOA stretch in `3e_qaoa_vs_classical.ipynb`. We gave QAOA a small version of the problem, choosing which links get QKD on a budget, at 10 and 12 qubits, and compared it with classical methods.

- The exact solver and the greedy method found the best answer every time, in about 0.01 seconds.
- Standard QAOA at 10 qubits returned the best answer on 0.24% to 0.31% of shots. Random guessing within the budget gets 0.40%, so standard QAOA did worse than guessing.
- XY-mixer QAOA did better, up to 1.68% at 10 qubits and 0.29% at 12 qubits.
- The standard QAOA circuits need 106 to 318 two-qubit gates at 10 qubits, which is too many for today's hardware.
- Through qBraid, the 10-qubit circuit stayed within the budget on 58% of shots on the qBraid QIR simulator and 52% on the IonQ simulator. It found the best answer on 0.10% of shots on both.

So we use classical optimization to plan the network, and quantum for the key exchange and the tap detection.

# Run Record

Every cloud run, labeled simulator, emulator or QPU, including the ones that failed. Runs on the local Aer simulator have no job ID and are not listed.

| Part | Run | Device | Type | Job ID | Shots | Status | Result |
|---|---|---|---|---|---|---|---|
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ simulator | Simulator | `ionq:ionq:sim:simulator-b095-qjob-6af88876c8f5265fb3f1bd01` | 200 | Completed | QBER 0.001 |
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-b095-qjob-6af88c54c8f5265fb3f1bdde` | 200 | Completed | QBER 0.004 |
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-b095-qjob-6af88b54c8f5265fb3f1bdaa` | 200 | Failed | Rejected before running: the circuit left one qubit unused |
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-b095-qjob-6af88ac6c8f5265fb3f1bd8d` | 200 | Failed | Open Quantum terms not accepted yet |
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-b095-qjob-6af88a4bc8f5265fb3f1bd6e` | 200 | Failed | Open Quantum terms not accepted yet |
| Step 1, Part 3 | BB84, 16 rounds in one circuit | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-b095-qjob-6af8896cc8f5265fb3f1bd3a` | 200 | Failed | Open Quantum account not connected yet |
| Step 2, Part 5 | Grover, N=4 | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af7e58ef15852ed27b72b26` | 200 | Completed | 200/200 on key (100%) |
| Step 2, Part 5 | Grover, N=8 | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af86a41c8f5265fb3f1b033` | 200 | Completed | 158/200 on key (79%) |
| Step 2, Part 5 | Grover, N=16 | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af7e25ef15852ed27b72a6b` | 200 | Completed | 87/200 on key (44%) |
| Step 2, Part 5 | Grover, N=16 | Quantinuum H2 emulator | Emulator | `quantinuum:quantinuum:sim:h2-emulator-0ad7-qjob-6af86c52c8f5265fb3f1b0ee` | 200 | Completed | 165/200 on key (82.5%) |
| Step 3, Part 3 | Teleportation link | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-b095-qjob-6af89604c8f5265fb3f1cbf3` | 200 | Completed | Qubit 2 read 0 on 195/200 |
| Step 3, Part 3 | Teleportation link, earlier run | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-b095-qjob-6af7d2bdf15852ed27b723ed` | 200 | Completed | Qubit 2 read 0 on 197/200 |
| Step 3, Part 3 | BB84 link, quiet | qBraid QIR simulator | Simulator | `qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8f6a3c8f5265fb3f21786` | 200 | Completed | QBER 0.000 |
| Step 3, Part 3 | BB84 link, quiet | IonQ simulator (aria-1 noise model) | Simulator | `ionq:ionq:sim:simulator-91f5-qjob-6af8f6afc8f5265fb3f2178e` | 200 | Completed | QBER 0.000 |
| Step 3, Part 3 | BB84 link, fully tapped | qBraid QIR simulator | Simulator | `qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8f6c0c8f5265fb3f2179e` | 200 | Completed | QBER 0.426 |
| Step 3, Part 3 | BB84 link, fully tapped | IonQ simulator (aria-1 noise model) | Simulator | `ionq:ionq:sim:simulator-91f5-qjob-6af8f6ccc8f5265fb3f217a4` | 200 | Completed | QBER 0.433 |
| Step 3, Part 3 | Attack test, random bits for Alice and Bob | qBraid QIR simulator | Simulator | `qbraid:qbraid:sim:qir-sv-0ad7-qjob-6af924c8c8f5265fb3f2389a` | 3 | Completed | 36 random bits, used for every attack run below |
| Step 3, Part 3 | Attack test, quiet | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-0ad7-qjob-6af924e0c8f5265fb3f238b0` | 200 | Completed | QBER 0.002, click yield 1.00 |
| Step 3, Part 3 | Attack test, full tap (also scored as blinding) | IonQ Forte 1 (Open Quantum) | QPU | `openquantum:ionq:qpu:forte-1-0ad7-qjob-6af9277bc8f5265fb3f23ba1` | 200 | Completed | Tap: QBER 0.188, click yield 1.00. Blinding: QBER 0.002, click yield 0.62 |
| Step 3, Part 3 | Attack test, quiet | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af9325fc8f5265fb3f2446f` | 200 | Completed | QBER 0.000, click yield 1.00 |
| Step 3, Part 3 | Attack test, partial tap | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af9326fc8f5265fb3f24483` | 200 | Completed | QBER 0.000, click yield 1.00 |
| Step 3, Part 3 | Attack test, denial of service | IonQ simulator (forte-1 noise model) | Simulator | `ionq:ionq:sim:simulator-0ad7-qjob-6af93280c8f5265fb3f24489` | 200 | Completed | QBER 0.677, click yield 1.00 |
| Step 3, Stretch | QAOA, 10 qubits | qBraid QIR simulator | Simulator | `qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8fab9c8f5265fb3f21a35` | 1,000 | Completed | Within budget on 58% of shots, best answer on 0.10% |
| Step 3, Stretch | QAOA, 10 qubits | IonQ simulator (aria-1 noise model) | Simulator | `ionq:ionq:sim:simulator-91f5-qjob-6af8facec8f5265fb3f21a47` | 1,000 | Completed | Within budget on 52% of shots, best answer on 0.10% |
