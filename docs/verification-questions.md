# Verification questions

Use these to test retrieval and citation quality once RAG is wired up. Each question has a **check** you can confirm by opening the PDF.

---

## AgentScore — Estevez et al. (2026)

**File:** `data/papers/Estevez_2026_AgentScore.pdf`

1. **What is the name of the method introduced in this paper, and what two roles does the LLM play in it?**
   - **Check:** AgentScore. The LLM proposes candidate rules; a deterministic verification-and-selection loop enforces validity and deployability. (Abstract, p. 1)

2. **How many clinical prediction tasks is AgentScore evaluated on, and which two public EHR databases do they come from?**
   - **Check:** Eight tasks from MIMIC-IV and eICU. (Abstract / Section 4)

3. **What example clinical scoring system is used repeatedly in the introduction to motivate deployability requirements?**
   - **Check:** CURB-65. (Introduction, p. 1)

4. **What metric does the paper use as an example empirical utility U(r) when describing rule selection?**
   - **Check:** AUROC. (Section 3 / Algorithm 1)

5. **Does the LLM receive patient-level records during rule proposal?**
   - **Check:** No — it receives a dataset description and tool-mediated aggregate statistics only. (Figure 2 caption / Section 4)

---

## HACHI — Feng et al. (2026)

**File:** `data/papers/Feng_human_ai_co_design.pdf`

1. **What does HACHI stand for, and what form do its learned concepts take?**
   - **Check:** Human-AI Co-design for Clinical Prediction Models (framework name: HACHI). Concepts are simple yes/no questions used in linear models. (Abstract, p. 1)

2. **Which two real-world clinical prediction tasks does the paper evaluate?**
   - **Check:** Acute kidney injury (AKI) and traumatic brain injury (TBI). (Abstract / Section 1)

3. **Where is the HACHI code repository hosted?**
   - **Check:** `http://github.com/jjfenglab/HACHI` (Abstract)

4. **What widely used TBI rule does the paper compare against in the trauma case study?**
   - **Check:** PECARN (Pediatric Emergency Care Applied Research Network). (Introduction / Methods)

5. **What interpretable baseline score families are cited as still popular in clinical practice (ICU mortality and TBI examples)?**
   - **Check:** SOFA (ICU mortality), PECARN and NEXUS (TBI). (Introduction, p. 1)

---

## AutoScore — Xie et al. (2020)

**File:** `data/papers/auto_score.pdf`

1. **How many modules does the AutoScore framework comprise, and what are they?**
   - **Check:** Six: variable ranking, variable transformation, score derivation, model selection, score fine-tuning, and model evaluation. (Abstract / Methods)

2. **Which hospital's EHR data is used for the mortality prediction demonstration?**
   - **Check:** Beth Israel Deaconess Medical Center (BIDMC). (Abstract / Methods)

3. **How many ICU admission episodes are in the study cohort?**
   - **Check:** 44,918. (Results / Table 1)

4. **What AUC does the nine-variable AutoScore model achieve, and how many variables does the compared logistic regression model use?**
   - **Check:** AUC 0.780 (95% CI 0.764–0.798) with nine variables vs. logistic regression AUC 0.778 with 24 variables. (Abstract / Results)

5. **What is the in-hospital mortality rate in the cohort (approximately)?**
   - **Check:** 8.8% (3,958 / 44,918). (Results)

---

## Cross-paper questions

These test whether retrieval can compare related work across your corpus.

1. **All three papers target interpretable clinical scoring or prediction. Which ones use LLM agents as part of the pipeline?**
   - **Check:** AgentScore and HACHI. AutoScore (2020) predates LLM agents and uses classical ML modules. (Compare abstracts)

2. **Which papers evaluate on MIMIC or Beth Israel Deaconess data?**
   - **Check:** AgentScore uses MIMIC-IV; AutoScore uses BIDMC (MIMIC's source hospital). HACHI uses its own multi-site EHR cohorts for AKI/TBI. (Methods sections)

3. **Which paper explicitly frames the problem as searching a discrete space of rule sets or concepts rather than training an unconstrained black-box model?**
   - **Check:** AgentScore (discrete rule-set search) and HACHI (concept selection from clinical notes). AutoScore uses variable ranking + score derivation modules. (Introductions)
