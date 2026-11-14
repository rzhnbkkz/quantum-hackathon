Step 3 - Secure the Grid Link

Part 1: Building the Teleportation Circuit

The team built a small quantum teleportation circuit to test how a quantum state can be transferred from Alice to Bob. Qubit 0 holds the state Alice wants to send. The circuit prepares a test state using RY(1.0) and RZ(0.7). Qubits 1 and 2 form an entangled pair shared between Alice and Bob.

Alice entangles her qubit with qubit 1 and then measures them. Bob uses the two results to apply corrections to qubit 2. In this circuit, the measurements are placed at the end and the corrections are controlled by Alice's qubits. This uses deferred measurement so the circuit can run on the available simulators.

Part 2: Results

On the local simulator, qubit 2 was measured as 0 in all 1,024 shots after the circuit reversed the state preparation. The counts were `{'001': 253, '011': 265, '000': 244, '010': 262}`. The first bit in each displayed result corresponds to qubit 2, so every listed outcome has qubit 2 equal to 0.

The IonQ simulator measured qubit 2 as 0 in 197 out of 200 shots, or 98.5% of the time. Its job ID was `ionq:ionq:sim:simulator-b095-qjob-6af7d2bdf15852ed27b723ed`. This was a simulator run, not a physical hardware run.

Part 3: What the Result Shows

The result suggests that the circuit transferred the test state successfully in the ideal local simulation. The IonQ simulator result was close, with three shots where qubit 2 did not return 0 after the inverse state preparation. These results apply to this circuit and test state; they do not show that every possible state or a real communication link would work the same way.

Part 4: Limits and Use in the Grid

This is a teleportation demonstration, not a working grid communication system. Teleportation requires Alice and Bob to share an entangled pair in advance and requires classical communication of Alice's measurement results. It does not send classical grid data directly, encrypt SCADA traffic, or by itself detect an intruder.

A real utility link would also need authenticated classical communication, reliable quantum equipment, and protection for the devices at both ends. The circuit shows a quantum communication idea, but it does not establish that teleportation would be a practical or cost-effective way to protect links in a small grid.
