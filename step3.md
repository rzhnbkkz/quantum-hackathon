# Step 3 - Design the Network

## Part 1: Architecture

We designed a small made-up utility network. It has 2 control centers, 1 communications hub and 6 substations (DS1 to DS6). The link lengths are our own guesses for a city-sized network. They are not real EPB data.

| Link | Length (our guess) | Protection |
|---|---|---|
| Main control to hub | 8 km | PQC + optional QKD pilot |
| Backup control to hub | 12 km | PQC |
| Hub to DS1 | 6 km | PQC |
| DS1 to DS4 | 9 km | PQC |
| Hub to DS2 | 7 km | PQC |
| DS2 to DS5 | 11 km | PQC |
| Hub to DS3 | 5 km | PQC |
| DS3 to DS6 | 14 km | PQC |
| Backup control to DS3 | not set | PQC (proposed backup route) |

We put post-quantum cryptography (PQC) on every link. It works on the equipment and fiber the utility already has, so it is the cheapest way to cover all 6 substations. We would use ML-KEM (FIPS 203) for exchanging keys and ML-DSA (FIPS 204) for signatures.

We only use QKD on one link, main control to hub, and only as an optional pilot. QKD works between two points, so every extra substation would need its own QKD equipment. That adds up fast for a utility on a tight budget.

Trusted nodes: on a long QKD path, the key has to be unlocked and re-locked at each stop in the middle. That means every stop has to be trusted. Our pilot is one short link, so it does not need any trusted nodes.

Distance: QKD makes keys more slowly as the fiber gets longer and loses more light. That is why we picked a short link for the pilot.

Timing: the two ends of a QKD link have to agree on time so they can match what was sent with what was received. QKD does not give the substations their time. The utility would keep using the clocks it already has.

Things our design does not fix: if the fiber is cut, the link needs another path. Both control centers go through the same hub, so if the hub fails, the backup center does not help. That is why we proposed one backup route to DS3 that skips the hub. We have not checked if that route is possible.

## Part 2: Assumptions and Tradeoffs

- The network and the link lengths are made up.
- We assumed the utility already has fiber on these links. We did not verify this.
- We did not measure fiber loss or QKD key rate. Those would need to be measured before buying QKD equipment.
- PQC is cheap, but it depends on math problems that we believe are hard. QKD depends on physics, but it needs special hardware, spare fiber and trained staff.
- QKD still needs normal authentication, so it does not replace PQC.

Numbers from the EPB field test (Evans et al., 2021): the test network was about 22 km long and had three QKD links of 3.4 km, 10.2 km and 8.3 km. The fiber loss on those links was 1.3 dB, 3.1 dB and 2.9 dB. Two of the links made secret key at about 1,310 and 1,892 bits per second, with error rates of 3.9% and 1.4%. After the keys were relayed through the trusted nodes, the whole network produced 115 bits per second, which is about one 256-bit key every two seconds. The test ran for 28 hours.

Our 8 km pilot link is in the same range as those links, but we have not measured its loss. A key rate like that is enough to keep refreshing encryption keys. It is not enough to encrypt all the traffic with QKD key directly.

Source: Evans et al., "Trusted Node QKD at an Electrical Utility," IEEE Access, 2021. https://arxiv.org/abs/2103.09877

## Part 3: Working Prototype

We picked Option B and built the teleportation circuit in `3_secure_grid_link.ipynb`.

The circuit sends the state of qubit 0 to qubit 2. First we entangle qubits 1 and 2. Then Alice links her message qubit to her half of the pair, and Bob's qubit gets two corrections. To check it, we undo the state on qubit 2 at the end. If the link works, qubit 2 reads 0 every time.

On the local simulator, qubit 2 read 0 on 1,024 of 1,024 shots. On the IonQ simulator with noise, it read 0 on 195 of 200 shots. The job ID was `ionq:ionq:sim:simulator-b095-qjob-6af89604c8f5265fb3f1cbf3`.

These are simulator results. We did not run this on real hardware. All three qubits are on one chip, so it shows the logic works but not that it works over a distance.

This could help with the trusted node problem. In QKD, every stop in the middle has to unlock the key and lock it again, so every stop has to be trusted. With teleportation, a middle stop only passes entanglement along and never holds the key. That needs quantum repeaters, which utilities cannot buy yet, so our design keeps QKD to one short link.

## Part 4: Rollout Plan

1. First: make a list of where the utility uses RSA and elliptic-curve cryptography. Fix firmware signing first, since a fake update would do the most damage. Turn on PQC at the control centers and the hub.
2. Next: add PQC at the substations, one branch at a time. Replace old gateways that cannot be updated.
3. Later: measure the fiber on the main control to hub link. Only try the QKD pilot if the measurements and the budget make sense.

## Part 5: Cost vs Security

| Option | Cost | What it protects | What is still exposed |
|---|---|---|---|
| Keep what they have | Nothing new | Attackers today | Traffic recorded now can be read later |
| PQC on every link | Software updates and some new gateways | All 8 links | Old devices behind the gateways, hub failure, fiber cuts |
| PQC + QKD pilot | Same as above plus QKD hardware, fiber and staff | Extra check for eavesdropping on 1 link | Same as PQC alone |

We recommend PQC on every link. It protects the whole network for the least money. The QKD pilot only adds protection to one link that PQC already covers, so it should wait until the fiber has been measured.

These costs are our guesses. We looked for public prices for QKD equipment and did not find any, because the vendors do not list them. A real comparison would need a quote.

## Stretch

We did not do the QAOA stretch.
