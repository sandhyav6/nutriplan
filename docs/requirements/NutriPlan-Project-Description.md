<!-- Auto-extracted from NutriPlan-Project-Description.docx. The .docx file is the authoritative source. -->

NutriPlan

Detailed Project Description

## 1. Introduction

NutriPlan is a web application that automatically generates personalized weekly meal plans and consolidated grocery lists for users, based on their dietary preferences, health goals, budget, and available cooking time. The system is designed in two phases. Phase 1 implements a deterministic rule engine that computes each user's nutrition profile and enforces hard constraints (diet type, allergies, budget, time) while ranking candidate meals. Phase 2 introduces an LLM personalization layer that operates on the rule engine's candidate meals, with its output passed back through the same constraint validator before anything reaches the user. This document describes the problem being solved, the intended users, the full functional and business logic scope, assumptions, dependencies, and the phased roadmap of the system.

## 2. Problem Statement

Individuals who want to eat healthier consistently struggle to plan meals that simultaneously satisfy several real-world constraints: nutritional balance, budget, dietary restrictions, time available for cooking, and variety. Existing solutions tend to specialize narrowly — most focus only on calorie tracking, or recommend generic plans that ignore budget or cooking time, and few adapt to a user's evolving preferences over time.

This gap causes three concrete problems for users:

- Time cost — manually planning balanced meals every day is tedious and is frequently abandoned.
- Financial waste — plans made without budget awareness lead to overspending and excess, unused groceries.
- Poor adherence — generic, non-adaptive recommendations feel repetitive and are dropped quickly.
NutriPlan addresses this by automating weekly plan and grocery list generation, filtered against user-specific constraints, and improving over time via an explicit feedback loop.

## 3. Project Goal & Objectives

Goal: To develop a web application that generates personalized weekly meal plans by jointly considering dietary preference, health goals, cooking time, and weekly budget — while minimizing food waste and simplifying grocery shopping.

Specific objectives:

- Allow users to create a profile capturing physical stats, activity level, dietary restrictions, health goals, budget, and time constraints.
- Translate the profile into a concrete nutrition target (calorie budget, protein target, BMI category) before any meal is selected.
- Generate a 7-day plan (breakfast, lunch, dinner, snacks) that satisfies all hard constraints.
- Auto-generate a de-duplicated, quantity-aggregated grocery list from the weekly plan.
- Let users react to meals (like / dislike / skip / favourite) and use this feedback to adjust future recommendations.
- Allow single-meal replacement without breaking the plan's overall budget, calorie target, or diet type.
- Provide a dashboard summarizing weekly calories, estimated spend, and meal statistics.
- Provide an admin panel to maintain the underlying food/recipe/nutrition data.
## 4. Project Scope

### 4.1 In Scope — Phase 1

| Module | Description |
| --- | --- |
| User Registration / Login | Standard auth: sign-up, login, session/token management. |
| User Profile | Stores age, gender, height, weight, activity level, dietary preference, allergies, health goal, weekly budget, cooking time. |
| Nutrition Profile Calculation | Derives BMI and an activity-adjusted calorie target from the profile before recommendation begins. |
| Meal Recommendation | Generates breakfast, lunch, dinner and snacks for all 7 days of the week. |
| Grocery List Generator | Combines ingredients across the week, removes duplicates, calculates total quantities. |
| Feedback System | Captures like, dislike, skip, favourite signals per meal as a weighted preference score. |
| Meal Replacement | Swaps a single meal while preserving budget, calorie target, and diet type. |
| Dashboard | Shows weekly calories, estimated spend, meal statistics, favourites. |
| Admin Panel | CRUD for foods, recipes, nutrition values, and categories. |

### 4.2 Out of Scope

- AI chatbot / conversational assistant
- Live grocery price feeds
- Barcode scanning
- Wearable device integration
- Machine-learning based recommendation engine
## 5. Assumptions

- The food/recipe database contains accurate, pre-calculated nutritional information.
- Users provide honest and reasonably accurate profile information.
- Ingredient prices are relatively stable across the planning period (no live price feed in Phase 1).
- Cooking time estimates exist for every recipe in the database.
- Users have internet connectivity while using the application.
- Each meal belongs to exactly one meal category (breakfast / lunch / dinner / snack).
- Users prepare meals themselves (no third-party delivery/integration assumed).
## 6. Dependencies

### 6.1 Internal Dependencies

- Food Database
- Recipe Database
- User Database
- Feedback Database
- Recommendation (Rule) Engine
### 6.2 External Dependencies

- Nutrition APIs
- Food Price APIs
- LLM API (for reasoning layer)
- Recipe APIs
- Authentication service (e.g., OAuth provider)
## 7. Functional Overview

The end-to-end user flow is linear and feedback-driven:

Register → Create Profile → Calculate Nutrition Profile → Generate Weekly Meal Plan → Generate Grocery List → Submit Feedback → Feedback Improves Future Recommendations

## 8. Nutrition Profile Calculation

Before any meal is selected, the raw profile inputs are converted into concrete numeric targets. This keeps the recommendation logic downstream working with numbers rather than re-interpreting raw fields every time.

### 8.1 Activity-Adjusted Calorie Target

Activity level scales the baseline calorie estimate:

- Sedentary → approx. 1800 kcal/day
- Moderately Active → approx. 2300 kcal/day
- Very Active → approx. 2800 kcal/day
The recommendation engine then filters and ranks meals against this target, not against a fixed default.

### 8.2 BMI

BMI is computed from height and weight (BMI = Weight ÷ Height²) and used as a secondary signal — for example, a BMI above 25 raises the ranking priority of weight-loss-oriented meals. It informs ranking; it does not gate meals outright.

### 8.3 Goal → Nutrition Target → Meal Selection

Health goal is not mapped directly to a food category. It first resolves to a nutrition target, and meal selection is filtered against that target:

- Muscle Gain → Protein ≥ 120g/day, Calories ≈ 2600 → meals meeting that target
- Weight Loss → Calories below target, Protein above minimum → meals meeting that target
- Maintenance → Balanced macros around the activity-adjusted target
## 9. Business Logic (Recommendation Pipeline)

| Stage | Logic |
| --- | --- |
| 1. Collect Inputs | Age, gender, weight, height, activity level, health goal, diet preference, allergies, budget, cooking time. |
| 2. Calculate Nutrition Profile | Derives BMI and activity-adjusted calorie target (Section 9); resolves health goal to a concrete protein/calorie target. |
| 3. Diet / Allergy Filter | Removes meals violating diet type or containing allergens (e.g., vegetarian profile removes chicken curry, fish fry, egg omelette). |
| 4. Candidate Meal Generation | Builds the pool of meals that satisfy the nutrition target from Stage 2. |
| 5. Budget Check | Weekly budget is broken down into a daily budget and a per-meal budget; if a meal exceeds its per-meal budget, it is replaced first. |
| 6. Cooking-Time Filter | Recipes exceeding the user's available time (e.g., >20 min when limit is 20 min) are excluded. |
| 7. Meal Ranking | Remaining candidates are scored and ordered using nutrition fit, budget fit, and feedback score (Section 11.3). |
| 8. Meal Variety Check | Recent meal history is compared against candidates by category similarity; a meal is swapped if its similarity score to a recently-served meal exceeds the threshold. |
| 9. Weekly Planner | Assembles the ranked, variety-checked candidates into a full 7-day plan. |
| 10. Grocery List Generation | Aggregates ingredient quantities across all 7 days (e.g., 200g + 300g chicken = 500g). |
| 11. Feedback Storage | Persists like / dislike / favorite / skip as a weighted score against each meal. |
| 12. Future Recommendation Adjustment | Rule-based re-weighting: higher-scored meals prioritized, lower-scored meals deprioritized. |

## 10. Rule Engine — Representative Rules

### 10.1 Core Rules

| Rule | Condition → Action |
| --- | --- |
| Rule 1 | IF diet = Vegetarian THEN only vegetarian meals are candidates. |
| Rule 2 | IF goal = Weight Loss THEN calories < target AND protein > minimum. |
| Rule 3 | IF meal cost > per-meal budget THEN replace with a lower-cost alternative first. |
| Rule 4 | IF cooking time limit = 15 min THEN recipe time ≤ 15 min. |
| Rule 5 | IF allergy = Peanuts THEN exclude all peanut-containing ingredients. |
| Rule 6 | IF BMI > 25 THEN weight-loss-oriented meals receive higher ranking priority. |
| Rule 7 | IF a candidate's category-similarity score to a recent meal exceeds the threshold THEN replace with a nutritionally similar alternative. |
| Rule 8 | IF a meal is a favorite THEN recommend nutritionally similar meals. |

### 10.2 Budget Breakdown

Weekly Budget → Daily Budget → Per-Meal Budget. Deriving the per-meal budget up front (rather than checking only the weekly total at the end) makes single-meal replacement straightforward, since each candidate meal can be checked against its own budget independently.

### 10.3 Feedback Scoring

Feedback is stored as a weighted score rather than a discrete label, so it can directly drive ranking:

- Favorite → +3
- Like → +1
- Skip → −1
- Dislike → −3
Storing feedback this way also means the data is already in a usable form if the ranking stage is later handed to an LLM or ML model, without a separate migration step.

## 11. Phase 2 — LLM-Powered NutriPlan (Future Roadmap)

Phase 2 does not replace the rule engine — the rule engine still produces the candidate meal plans and still owns every hard, non-negotiable constraint (diet, allergies, budget). An LLM personalization layer sits between candidate generation and the user, and its output is passed back through the same constraint validator before it is shown to anyone.

Revised architecture: User → User Profile → Rule Engine → Candidate Meal Plans → LLM Personalization Layer → Constraint Validator → Final Weekly Plan.

Placing the constraint validator after the LLM, rather than trusting the LLM's output directly, matters because LLMs can hallucinate. If the LLM layer suggests a substitution containing peanuts for a user with a peanut allergy, the validator catches and rejects it before it is ever presented — the same non-negotiable rules from Phase 1 still apply, just applied one stage later in the pipeline.

Planned LLM-driven capabilities:

- Explaining why specific meals were selected (e.g., 'chosen for your protein goal, ready in under 20 minutes')
- Understanding natural-language preference changes (e.g., 'I don't feel like rice this week')
- Handling vague, mood-based requests (e.g., 'something comforting but healthy')
- Suggesting ingredient substitutions
- Generating cooking instructions and tips
- Answering conversational nutrition questions
- Learning long-term preferences beyond simple like/dislike signals
Over time, portions of the handcrafted rule set may be replaced by LLM reasoning combined with embeddings/retrieval over the recipe database — while allergy, dietary, and budget constraints remain enforced through the same separate, non-negotiable validation layer regardless of the LLM's output.

> **[Image in source document – review the .docx manually]**

> **Manual transcription of the Work Breakdown Structure image (reviewed by hand; the image in the .docx is authoritative):**
>
> 1. **Project Planning** – project initiation (problem statement, stakeholders, objectives, scope, Agile SDLC); planning (WBS, Gantt chart, effort estimation, risk identification, sprint planning). Deliverables: project charter, WBS, Gantt chart, risk register.
> 2. **Requirements Engineering** – elicitation, analysis (prioritise/validate), documentation (prepare and finalise SRS). Deliverables: requirement specification, FR/NFR lists, SRS.
> 3. **Requirement Modelling** – structural (ER diagram), functional (context diagram, DFD level 0/1), behavioural (state transition and activity diagrams).
> 4. **Object-Oriented Design** – use case modelling, class design, interaction design (sequence, communication), architectural design (package, component, deployment diagrams).
> 5. **UI / UX Design** – user personas, storyboarding, user journeys; low/high fidelity wireframes, interactive prototype.
> 6. **Development (Agile Sprints)** – Sprint 1: authentication module, user profile module (profile, preferences); Sprint 2: food database module, recommendation engine; Sprint 3: meal planner module, grocery list module; Sprint 4: feedback module, dashboard module. Deliverables: working software (incremental after each sprint), complete application.
> 7. **Testing** – functional (unit, integration, system, user acceptance), non-functional (performance, security, usability, reliability), defect management (bug reporting, fixing, regression testing). Deliverables: test plan, test cases, test report, defect log.
> 8. **Deployment** – configure database, deploy backend, deploy frontend; documentation (user manual, technical documentation, API documentation); final review (demonstration, presentation, final submission).
