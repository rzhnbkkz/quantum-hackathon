## Hardware attack runs (submitted through the qBraid MCP server, org tennessee-quantum-hackathon, 0 credits)

Same 12-round BB84 instance (seed 0) for every attack. QBER is computed on the sifted rounds and the click yield on the matched-basis rounds that produced a result.

| Run | Device | Job ID | Shots | QBER | Click yield |
|---|---|---|---|---|---|
| QRNG bits | qbraid:qbraid:sim:qir-sv | qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8e4a7c8f5265fb3f21089 | 3 | – | – |
| quiet | qbraid:qbraid:sim:qir-sv | qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8e4aac8f5265fb3f2108d | 200 | 0.000 | 1.00 |
| tap (intercept-resend, all rounds) | qbraid:qbraid:sim:qir-sv | qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8e4aec8f5265fb3f21092 | 200 | 0.353 | 1.00 |
| blinding (same job as tap, Bob post-selected) | qbraid:qbraid:sim:qir-sv | (same as tap) | 200 | 0.000 | 0.29 |
| partial (3 of 12 rounds) | qbraid:qbraid:sim:qir-sv | qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8e4b2c8f5265fb3f2109e | 200 | 0.082 | 1.00 |
| dos (scrambling) | qbraid:qbraid:sim:qir-sv | qbraid:qbraid:sim:qir-sv-91f5-qjob-6af8e4b7c8f5265fb3f210a6 | 200 | 0.789 | 1.00 |
| tap, cross-check | ionq:ionq:sim:simulator | ionq:ionq:sim:simulator-91f5-qjob-6af8e4bbc8f5265fb3f210ab | 200 | (returned probabilities, not sampled shots) | – |

Reading: the tap, partial and DoS attacks all raise QBER over the quiet baseline. The partial attack (8%) stays under the 11% abort line, so a single batch may let it through. That's why 3d uses a windowed/CUSUM alarm. Blinding leaves QBER at 0 but cuts the click yield to 29%: only a click-rate monitor sees it. With 12 rounds Eve's basis is fixed per round, so a tap's QBER lands anywhere between 0% and 50% depending on how many sifted rounds she guessed wrong. The 25% figure only holds on average over many rounds.
