 Step 1: BB84

I ran BB84 twice, once with Eve listening in and once without her. Alice and Bob each picked a basis for every round. I only kept the rounds where they picked the same basis. The error rate (QBER) is how often their bits disagreed in those rounds. Without Eve, the error rate was **0%**. With Eve, it went up to 23.7%. I also ran the batched circuit without Eve on the local simulator and the IonQ simulator. Both came back with 0%. Eve measured each qubit in a random basis, then sent Bob a new one based on what she got. She picked the wrong basis about half the time. When that happened, Bob had a 50% chance of getting the wrong bit on a round he and Alice kept. That puts the expected error rate around 25%, which is close to what I got. That’s why Alice and Bob check some of their bits before using the key. A high error rate tells them something is off, but noise can cause errors too.

 The IonQ simulator job ID: `ionq:ionq:sim:simulator-b095-qjob-6af7c852f15852ed27b72101`
