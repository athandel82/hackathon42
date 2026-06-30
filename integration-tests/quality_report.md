# Analyze Agent — Reference Question Quality Report

- **Repo:** `patrikja__autosar__master` (from https://github.com/patrikja/autosar@master)
- **Questions:** 10 (aligned to `knowledge_base/validation/questions.md`)
- **Engine:** deterministic reference agent over the real KB (Bedrock stubbed; see README).

> Scoring compares `what_breaks.impacted` and the resolved target type against the validation bank's ground truth.

## Summary

| ID | Bank | Category | Change request | Target (type) | Impacted | Cost | Top risk | Verdict |
|----|------|----------|----------------|---------------|----------|------|----------|---------|
| Q1 | Q05 | blast-radius | If we remove the Door component, what breaks? | Door (APPLICATION-SW-COMPONENT-TYPE) | CombinedStatusLockedLeftIPdu, CombinedStatusLockedRightIPdu, CombinedStatusOpenLeftIPdu, CombinedStatusOpenRightIPdu, DoorControl, EDC | 40–240 engineer-hours / neutral | Network signal source affected (high) | ✅ match |
| Q2 | — | blast-radius | What is the impact of removing the DoorControl component? | DoorControl (APPLICATION-SW-COMPONENT-TYPE) | CombinedStatusLockedLeftIPdu, CombinedStatusLockedRightIPdu, CombinedStatusOpenLeftIPdu, CombinedStatusOpenRightIPdu, EDC | 40–200 engineer-hours / neutral | Network signal source affected (high) | ✅ match |
| Q3 | Q06 | blast-radius | What is the impact of removing the IoHwAb service component? | IoHwAb (SERVICE-SW-COMPONENT-TYPE) | DoorControl, EDC | 40–160 engineer-hours / neutral | Network signal source affected (high) | ✅ match |
| Q4 | — | blast-radius | What breaks if we remove the EDC composition? | EDC (COMPOSITION-SW-COMPONENT-TYPE) | ∅ | 40–80 engineer-hours / favorable | Downstream components require rework (medium) | ✅ correct (root) |
| Q5 | Q04 | dependency | What is affected if we change the DoorStatus interface? | DoorStatus (SENDER-RECEIVER-INTERFACE) | Door, DoorControl | 40–160 engineer-hours / neutral | Downstream components require rework (high) | ✅ match |
| Q6 | — | dependency | What is affected if we change the DoorCommands interface? | DoorCommands (CLIENT-SERVER-INTERFACE) | Door, DoorControl | 40–160 engineer-hours / neutral | Downstream components require rework (high) | ✅ match |
| Q7 | Q07 | signal-flow | What breaks if we modify the CombinedStatus interface? | CombinedStatus (SENDER-RECEIVER-INTERFACE) | CombinedStatusLockedLeftIPdu, CombinedStatusLockedRightIPdu, CombinedStatusOpenLeftIPdu, CombinedStatusOpenRightIPdu, DoorControl, EDC | 40–240 engineer-hours / neutral | Network signal source affected (high) | ✅ match |
| Q8 | — | dependency | What is the impact of removing the DigitalServiceWrite interface? | DigitalServiceWrite (CLIENT-SERVER-INTERFACE) | DoorControl, IoHwAb | 40–160 engineer-hours / neutral | Downstream components require rework (high) | ✅ match |
| Q9 | Q11 | de-content | De-content the right door: what becomes obsolete if we remove the DoorRight instance? | DoorRight (SW-COMPONENT-PROTOTYPE) | ∅ | 40–80 engineer-hours / favorable | Downstream components require rework (medium) | ⚠️ limitation |
| Q10 | Q08 | signal-flow | What is the network/bus impact of removing the Door component? | Door (APPLICATION-SW-COMPONENT-TYPE) | CombinedStatusLockedLeftIPdu, CombinedStatusLockedRightIPdu, CombinedStatusOpenLeftIPdu, CombinedStatusOpenRightIPdu, DoorControl, EDC | 40–240 engineer-hours / neutral | Network signal source affected (high) | ✅ match |

## Per-question detail

### Q1 — If we remove the Door component, what breaks?

- **Bank question:** Q05  |  **category:** blast-radius
- **Resolved target:** `/Demo/Door/Door` — Door (APPLICATION-SW-COMPONENT-TYPE)
- **Summary:** 2 component(s) and 4 signal chain(s) impacted by changing Door.
- **Impacted (6):**
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on Door; removing/changing it breaks this relationship.
  - `/Demo/EDC/EDC` — COMPOSITION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — EDC depends on Door; removing/changing it breaks this relationship.
  - `CombinedStatusLockedLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusLockedLeftIPdu.
  - `CombinedStatusOpenLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusOpenLeftIPdu.
  - `CombinedStatusLockedRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusLockedRightIPdu.
  - `CombinedStatusOpenRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusOpenRightIPdu.
- **Expected impacted (ground truth):** DoorControl, EDC → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–240 engineer-hours / neutral
- **Risks:** Network signal source affected (high, revalidate=True); Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q2 — What is the impact of removing the DoorControl component?

- **Bank question:** —  |  **category:** blast-radius
- **Resolved target:** `/Demo/DoorControl/DoorControl` — DoorControl (APPLICATION-SW-COMPONENT-TYPE)
- **Summary:** 1 component(s) and 4 signal chain(s) impacted by changing DoorControl.
- **Impacted (5):**
  - `/Demo/EDC/EDC` — COMPOSITION-SW-COMPONENT-TYPE, 1 hop(s), severity **medium**, domain body/doors — EDC depends on DoorControl; removing/changing it breaks this relationship.
  - `CombinedStatusLockedLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — DoorControl feeds this chain; a cut severs CombinedStatusLockedLeftIPdu.
  - `CombinedStatusOpenLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — DoorControl feeds this chain; a cut severs CombinedStatusOpenLeftIPdu.
  - `CombinedStatusLockedRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — DoorControl feeds this chain; a cut severs CombinedStatusLockedRightIPdu.
  - `CombinedStatusOpenRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — DoorControl feeds this chain; a cut severs CombinedStatusOpenRightIPdu.
- **Expected impacted (ground truth):** EDC → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–200 engineer-hours / neutral
- **Risks:** Network signal source affected (high, revalidate=True); Downstream components require rework (medium, revalidate=True)
- **Confidence:** medium

### Q3 — What is the impact of removing the IoHwAb service component?

- **Bank question:** Q06  |  **category:** blast-radius
- **Resolved target:** `/Demo/Services/IoHwAb/IoHwAb` — IoHwAb (SERVICE-SW-COMPONENT-TYPE)
- **Summary:** 2 component(s) and 0 signal chain(s) impacted by changing IoHwAb.
- **Impacted (2):**
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on IoHwAb; removing/changing it breaks this relationship.
  - `/Demo/EDC/EDC` — COMPOSITION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — EDC depends on IoHwAb; removing/changing it breaks this relationship.
- **Expected impacted (ground truth):** DoorControl, EDC → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–160 engineer-hours / neutral
- **Risks:** Network signal source affected (high, revalidate=True); Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q4 — What breaks if we remove the EDC composition?

- **Bank question:** —  |  **category:** blast-radius
- **Resolved target:** `/Demo/EDC/EDC` — EDC (COMPOSITION-SW-COMPONENT-TYPE)
- **Summary:** 0 component(s) and 0 signal chain(s) impacted by changing EDC.
- **Impacted (0):**
- **Cost:** BOM saved 5–25 USD; eng rework 40–80 engineer-hours / favorable
- **Risks:** Downstream components require rework (medium, revalidate=False)
- **Confidence:** medium

### Q5 — What is affected if we change the DoorStatus interface?

- **Bank question:** Q04  |  **category:** dependency
- **Resolved target:** `/Demo/Interfaces/DoorStatus` — DoorStatus (SENDER-RECEIVER-INTERFACE)
- **Summary:** 2 component(s) and 0 signal chain(s) impacted by changing DoorStatus.
- **Impacted (2):**
  - `/Demo/Door/Door` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — Door depends on DoorStatus; removing/changing it breaks this relationship.
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on DoorStatus; removing/changing it breaks this relationship.
- **Expected impacted (ground truth):** Door, DoorControl → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–160 engineer-hours / neutral
- **Risks:** Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q6 — What is affected if we change the DoorCommands interface?

- **Bank question:** —  |  **category:** dependency
- **Resolved target:** `/Demo/Interfaces/DoorCommands` — DoorCommands (CLIENT-SERVER-INTERFACE)
- **Summary:** 2 component(s) and 0 signal chain(s) impacted by changing DoorCommands.
- **Impacted (2):**
  - `/Demo/Door/Door` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — Door depends on DoorCommands; removing/changing it breaks this relationship.
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on DoorCommands; removing/changing it breaks this relationship.
- **Expected impacted (ground truth):** Door, DoorControl → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–160 engineer-hours / neutral
- **Risks:** Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q7 — What breaks if we modify the CombinedStatus interface?

- **Bank question:** Q07  |  **category:** signal-flow
- **Resolved target:** `/Demo/Interfaces/CombinedStatus` — CombinedStatus (SENDER-RECEIVER-INTERFACE)
- **Summary:** 2 component(s) and 4 signal chain(s) impacted by changing CombinedStatus.
- **Impacted (6):**
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on CombinedStatus; removing/changing it breaks this relationship.
  - `/Demo/EDC/EDC` — COMPOSITION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — EDC depends on CombinedStatus; removing/changing it breaks this relationship.
  - `CombinedStatusLockedLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — CombinedStatus feeds this chain; a cut severs CombinedStatusLockedLeftIPdu.
  - `CombinedStatusOpenLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — CombinedStatus feeds this chain; a cut severs CombinedStatusOpenLeftIPdu.
  - `CombinedStatusLockedRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — CombinedStatus feeds this chain; a cut severs CombinedStatusLockedRightIPdu.
  - `CombinedStatusOpenRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — CombinedStatus feeds this chain; a cut severs CombinedStatusOpenRightIPdu.
- **Expected impacted (ground truth):** DoorControl, EDC → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–240 engineer-hours / neutral
- **Risks:** Network signal source affected (high, revalidate=True); Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q8 — What is the impact of removing the DigitalServiceWrite interface?

- **Bank question:** —  |  **category:** dependency
- **Resolved target:** `/Demo/Services/IoHwAb/DigitalServiceWrite` — DigitalServiceWrite (CLIENT-SERVER-INTERFACE)
- **Summary:** 2 component(s) and 0 signal chain(s) impacted by changing DigitalServiceWrite.
- **Impacted (2):**
  - `/Demo/Services/IoHwAb/IoHwAb` — SERVICE-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — IoHwAb depends on DigitalServiceWrite; removing/changing it breaks this relationship.
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on DigitalServiceWrite; removing/changing it breaks this relationship.
- **Expected impacted (ground truth):** DoorControl, IoHwAb → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–160 engineer-hours / neutral
- **Risks:** Downstream components require rework (high, revalidate=True)
- **Confidence:** medium

### Q9 — De-content the right door: what becomes obsolete if we remove the DoorRight instance?

- **Bank question:** Q11  |  **category:** de-content
- **Resolved target:** `/Demo/EDC/EDC/DoorRight` — DoorRight (SW-COMPONENT-PROTOTYPE)
- **Summary:** 0 component(s) and 0 signal chain(s) impacted by changing DoorRight.
- **Impacted (0):**
- **Cost:** BOM saved 5–25 USD; eng rework 40–80 engineer-hours / favorable
- **Risks:** Downstream components require rework (medium, revalidate=False)
- **Confidence:** medium

### Q10 — What is the network/bus impact of removing the Door component?

- **Bank question:** Q08  |  **category:** signal-flow
- **Resolved target:** `/Demo/Door/Door` — Door (APPLICATION-SW-COMPONENT-TYPE)
- **Summary:** 2 component(s) and 4 signal chain(s) impacted by changing Door.
- **Impacted (6):**
  - `/Demo/DoorControl/DoorControl` — APPLICATION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — DoorControl depends on Door; removing/changing it breaks this relationship.
  - `/Demo/EDC/EDC` — COMPOSITION-SW-COMPONENT-TYPE, 1 hop(s), severity **high**, domain body/doors — EDC depends on Door; removing/changing it breaks this relationship.
  - `CombinedStatusLockedLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusLockedLeftIPdu.
  - `CombinedStatusOpenLeftIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusOpenLeftIPdu.
  - `CombinedStatusLockedRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusLockedRightIPdu.
  - `CombinedStatusOpenRightIPdu` — I-SIGNAL-I-PDU, 2 hop(s), severity **high**, domain network — Door feeds this chain; a cut severs CombinedStatusOpenRightIPdu.
- **Expected impacted (ground truth):** CombinedStatusLockedLeftIPdu, CombinedStatusOpenRightIPdu → all present
- **Cost:** BOM saved 5–25 USD; eng rework 40–240 engineer-hours / neutral
- **Risks:** Network signal source affected (high, revalidate=True); Downstream components require rework (high, revalidate=True)
- **Confidence:** medium


## Notes on quality & known limitations

- **Component blast radius** (Q1–Q3) and **interface usage** (Q5–Q8) are computed from the precomputed KB graph and match the validation ground truth.
- **Q4 (EDC)** correctly returns an empty blast radius — EDC is the root composition, nothing depends on it.
- **Q9 (DoorRight instance de-content)** is a known limitation of the deterministic stub: instance/prototype-level analysis (right-door-only signals, mappings, connectors) needs the richer KB detail the real Bedrock agent would read. The bank's Q11 lists the full expected set.
- Cost and risk figures are heuristic (no BOM/labor data in ARXML), per the analyze architecture §13.
- These answers come from the deterministic reference agent, not a live Bedrock call; they exercise grounding/data-flow, not LLM reasoning quality.
