
Step 1 - Secure the Link

Part 1: BB84 and Eavesdropper Detection

The team built a BB84 simulation to show how two people can create a shared secret key and check whether someone may have intercepted the qubits. Alice generates random bits and randomly chooses a basis for each one. She encodes each bit as a qubit and sends it to Bob. Bob independently chooses a random basis to measure each qubit. Afterward, Alice and Bob compare their basis choices over a public channel and keep only the bits where they used the same basis. These remaining bits are called the sifted key.

The team tested an intercept-and-resend eavesdropper. Eve measures each qubit in a randomly chosen basis, then prepares a new qubit based on her result and sends it to Bob. If Eve chooses the wrong basis, her measurement can change the state. Alice and Bob estimate the quantum bit error rate (QBER) by comparing their sifted bits.

Part 2: Results

With no eavesdropper, the local simulator produced a QBER of 0.0. With Eve intercepting and resending the qubits, the QBER was 0.243, or about 24%. This is close to the expected error rate of about 25% for this attack: Eve chooses the wrong basis about half the time, and those wrong-basis measurements cause errors in about half of the affected sifted bits. The exact result can vary between runs because the bits, bases, and measurements are random.

The team also tested a batched circuit with 16 qubits and 200 shots. The local simulator gave a QBER of 0.0. The IonQ simulator run gave a QBER of 0.001. Its job ID was `ionq:ionq:sim:simulator-b095-qjob-6af88876c8f5265fb3f1bd01`.

The team then ran the batched circuit on the IonQ Forte 1 quantum processor through Open Quantum, using 200 shots. The hardware QBER was 0.004, or about 0.4%. Its job ID was `openquantum:ionq:qpu:forte-1-b095-qjob-6af88c54c8f5265fb3f1bdde`. This hardware run did not include Eve; the Eve result came from the local simulator.

Part 3: What the Result Shows

The comparison shows how an intercept-and-resend attack can raise the error rate in the sifted key. A higher QBER can warn Alice and Bob that the communication may have been disturbed. It does not identify who caused the errors: noise, transmission problems, or device errors could also raise QBER. A QBER of 0.0 in one run does not prove that nobody intercepted the qubits.

For this demonstration, a QBER around 10% or higher would be a useful warning threshold. It is well above the 0.4% hardware baseline from this run and below the roughly 25% expected from the simulated intercept-and-resend attack. This is only an illustrative threshold for these tests, not a setting for a real QKD system. A deployed system would need to account for its measured noise, sample size, and security requirements.

Part 4: Limits and Use in the Grid

This is a small demonstration of BB84, not a complete key distribution system. In a real deployment, Alice and Bob would need to authenticate their public discussion, compare a sample of the sifted key, and discard the tested bits. They would also need error correction and privacy amplification before using the remaining bits as a key.

BB84 can help protect a key exchange on a suitable quantum link, but it does not encrypt grid traffic by itself or secure every substation and control center. The resulting key would still need to be used by ordinary encryption equipment. These tests do not demonstrate a deployed fiber link or prove that QKD is the most cost-effective choice for a utility. A smaller or resource-limited grid would need to compare QKD’s cost and operating requirements with post-quantum cryptography.
