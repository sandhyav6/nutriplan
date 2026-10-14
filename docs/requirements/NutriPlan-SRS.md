<!-- Auto-extracted from NutriPlan-SRS.docx. The .docx file is the authoritative source. -->

Software Requirements Specification

for

NutriPlan – Adaptive Meal Planning Based on Lifestyle

Version 1.0 approved

Prepared by:

Anvita Arun, Sandhya Venkatesh, Saadhvi H

VIT Chennai

20/07/2026

Table of Contents

Table of Contents ii

Revision History ii

1. Introduction 1

1.1 Purpose 1

1.2 Document Conventions 1

1.3 Intended Audience and Reading Suggestions 1

1.4 Product Scope 1

1.5 References 1

2. Overall Description 2

2.1 Product Perspective 2

2.2 Product Functions 2

2.3 User Classes and Characteristics 2

2.4 Operating Environment 2

2.5 Design and Implementation Constraints 2

2.6 User Documentation 2

2.7 Assumptions and Dependencies 3

3. External Interface Requirements 3

3.1 User Interfaces 3

3.2 Software Interfaces 3

3.3 Communications Interfaces 3

4. System Features 4

4.1 System Feature 1 4

4.2 System Feature 2 (and so on) 4

5. Other Nonfunctional Requirements 4

5.1 Performance Requirements 4

5.2 Safety Requirements 5

5.3 Security Requirements 5

5.4 Software Quality Attributes 5

5.5 Business Rules 5

6. Other Requirements 5

Appendix A: Glossary 5

Appendix B: Analysis Models 5

Appendix C: To Be Determined List 6

Revision History

| Name | Date | Reason For Changes | Version |
| --- | --- | --- | --- |
| NutriPlan | 20/07/2026 | Initial | 1.0 |
|  |  |  |  |

1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document describes the functional and non-functional requirements for NutriPlan, a web application that generates personalized weekly meal plans and grocery lists. This document covers Release 1.0 (Phase 1), which implements the rule-based recommendation engine described in the project's Business Requirements Document. Phase 2 (LLM-powered reasoning layer) is explicitly out of scope for this release and is documented separately in Section 2.7 and Appendix C for planning purposes only.

### 1.2 Document Conventions

Functional requirements are labeled using the format REQ-<Feature Number>.<Sequence> (e.g., REQ-4.1.1). Each requirement is atomic, verifiable, and independently testable, consistent with Agile Definition of Done practices — each REQ is intended to map to one or more Agile user story acceptance criteria during backlog grooming. Priority levels (High / Medium / Low) are assigned per feature in Section 4 and are inherited by all requirements listed under that feature unless individually overridden. Bold text indicates a defined term (see Appendix A: Glossary). Currency values are expressed in Indian Rupees (₹) unless stated otherwise.

### 1.3 Intended Audience and Reading Suggestions

This document is intended for the following readers:

- Product Owner / Project Sponsor — to validate scope against the problem statement and goals.
- Scrum Master and Development Team — to derive sprint backlog items and user stories from Section 4.
- QA / Test Engineers — to derive test cases from the Functional Requirements and Section 5.
- UI/UX Designers — to reference Section 3.1 for interface expectations.
- Future maintainers and Phase 2 contributors — to understand Phase 1 boundaries before extending the system.
Readers unfamiliar with the project should read Sections 1 and 2 first for context, followed by Section 4 for feature-level detail relevant to their role. Section 5 and Appendix A should be referenced as needed.

### 1.4 Product Scope

NutriPlan is a web application that automatically generates personalized weekly meal plans and consolidated grocery lists based on a user's dietary preferences, health goals, allergies, weekly budget, and available cooking time. The system applies a deterministic rule engine (Section 4) to filter and select meals, track user feedback (like/dislike/skip/favorite), and refine future recommendations accordingly.

The objective is to reduce the time users spend planning meals, minimize grocery over-purchasing and food waste, and make consistent healthy eating more convenient — particularly for students, working professionals, families, and fitness enthusiasts who currently rely on manual planning or generic calorie-tracking apps that ignore budget, cooking time, or variety.

### 1.5 References

- NutriPlan Project Brief / Business Requirements Document (source document provided by Product Owner, 2026).
- IEEE Std 830-1998 — IEEE Recommended Practice for Software Requirements Specifications (template basis for this document).
## 2. Overall Description

### 2.1 Product Perspective

NutriPlan is a new, self-contained web application; it is not a follow-on to an existing product. It consists of a rule-based recommendation engine sitting between a user-facing web client and a set of internal data stores (Food, Recipe, User, and Feedback databases). The Phase 1 architecture is entirely internal and self-hosted; no external APIs are required for this release.

At a high level, the system architecture is:

- User (Web Client) → Application Server (Rule Engine + Business Logic) → Databases (User, Food, Recipe, Feedback) → Response (Meal Plan / Grocery List) back to User.
This SRS anticipates a future Phase 2 in which an LLM Reasoning Layer is introduced on top of the existing rule engine (see Section 2.7). The Phase 1 architecture is designed so that the rule engine's outputs (candidate meal plans) can later be passed to that layer without redesigning the core data model.

### 2.2 Product Functions

The major functions the product must perform are summarized below; detailed requirements are provided in Section 4.

- User Registration and Login
- User Profile Management (age, gender, height, weight, dietary preference, allergies, health goal, weekly budget, cooking time)
- Weekly Meal Recommendation (breakfast, lunch, dinner, snacks for 7 days)
- Grocery List Generation (ingredient aggregation, deduplication, quantity calculation)
- Feedback Capture (like, dislike, skip, favorite)
- Meal Replacement (swap a meal while preserving budget, calorie, and diet constraints)
- Dashboard (weekly calories, estimated spending, meal statistics, favorite meals)
- Admin Panel (manage foods, recipes, nutrition values, categories)
### 2.3 User Classes and Characteristics

| User Class | Description | Importance |
| --- | --- | --- |
| End User (Primary) | Students, working professionals, families, fitness enthusiasts, and individuals managing a diet plan. Uses profile setup, meal plans, grocery lists, and feedback features. Assumed to have basic web literacy and no technical expertise. | Critical |
| Nutrition Professional (Secondary) | Dieticians, nutrition coaches, and meal-planning consultants who may review or guide plans on behalf of end users in future releases. | Low (Phase 1); Medium (future) |
| Administrator | Manages the Food, Recipe, Nutrition, and Category data that powers the recommendation engine. Requires elevated privileges. | High |

### 2.4 Operating Environment

NutriPlan is delivered as a web application and must operate correctly within the following environment:

- Client: Modern evergreen web browsers (Chrome, Firefox, Edge, Safari — latest two major versions), desktop and mobile viewport widths.
- Server: Cloud-hosted or on-premises application server running the backend service and rule engine.
- Database: Relational or document database hosting User, Food, Recipe, and Feedback data stores.
- Connectivity: Requires an active internet connection for all client-server interactions (see Assumption in Section 2.7).
Specific hosting provider, server OS version, and database engine are implementation decisions to be finalized by the development team during sprint planning and are marked TBD in Appendix C.

### 2.5 Design and Implementation Constraints

- The system must enforce hard constraints (diet type, allergies, budget) as non-negotiable validation rules; these may never be overridden by soft/preference-based logic, including in any future Phase 2 LLM layer.
- Each meal must belong to exactly one meal category (breakfast, lunch, dinner, or snack), per the data model assumption in Section 2.7.
- Recommendation logic for Phase 1 must be deterministic and rule-based (IF–THEN); no machine learning or LLM inference is permitted in this release.
- The project follows an Agile SDLC process; requirements in Section 4 are expected to be decomposed into user stories and delivered iteratively across sprints, and this SRS should be treated as a versioned, living document updated as the backlog evolves.
- All monetary values are handled in Indian Rupees (₹) for Phase 1; multi-currency support is not required.
### 2.6 User Documentation

The following user-facing documentation is expected to accompany the delivered product:

- In-app onboarding guide for first-time profile setup.
- Online help / FAQ section covering meal replacement, grocery list usage, and feedback features.
- Administrator guide for managing the Food, Recipe, and Nutrition database via the Admin Panel.
Delivery format (in-app tooltips, a hosted help center, or a downloadable PDF) is TBD and should be confirmed with the Product Owner (see Appendix C).

### 2.7 Assumptions and Dependencies

#### Assumptions

- The food database contains accurate nutritional information.
- Users honestly and accurately provide their profile information.
- Recipe nutritional values are pre-calculated and available before meal generation.
- Ingredient prices are relatively stable across the planning period.
- Cooking time estimates are available for every recipe in the database.
- Internet connectivity is available to the user at all times of use.
- Each meal belongs to exactly one meal category.
- Users prepare meals themselves (the system does not manage delivery or takeout).
#### Dependencies

Internal:

- Food Database
- Recipe Database
- User Database
- Feedback Database
- Recommendation (Rule) Engine
External (Optional, Phase 2 only — not required for this release):

- Nutrition APIs
- Food Price APIs
- LLM API (for the Phase 2 Reasoning Layer described below)
- Recipe APIs
- Authentication service
## 3. External Interface Requirements

### 3.1 User Interfaces

The system shall provide a responsive web interface covering, at minimum, the following screens:

- Registration / Login screen
- Profile setup and edit screen (age, gender, height, weight, dietary preference, allergies, health goal, weekly budget, cooking time)
- Weekly Meal Plan view (7-day grid: breakfast, lunch, dinner, snacks)
- Meal detail view with like / dislike / skip / favorite controls and a Replace Meal action
- Grocery List view (aggregated, deduplicated ingredient list with quantities)
- Dashboard (weekly calories, estimated spending, meal statistics, favorite meals)
- Admin Panel (CRUD screens for Foods, Recipes, Nutrition Values, Categories)
All screens shall follow a consistent layout with standard navigation, form validation, and inline error messaging. Detailed wireframes and visual design standards are to be documented in a separate UI specification, not duplicated here.

### 3.2 Software Interfaces

| Interface | Description |
| --- | --- |
| User Database | Stores registration credentials and profile attributes (age, gender, height, weight, dietary preference, allergies, health goal, budget, cooking time). Read/write access required by the Profile and Auth features. |
| Food Database | Stores individual food items and their nutrition values (calories, protein, carbs, fats) and prices. Read access required by the Rule Engine; read/write access required by the Admin Panel. |
| Recipe Database | Stores recipes, their ingredient lists, quantities, preparation time, and category (breakfast/lunch/dinner/snack). Read access required by the Rule Engine; read/write access required by the Admin Panel. |
| Feedback Database | Stores per-user, per-meal feedback events (like, dislike, skip, favorite) with timestamps. Written by the Feedback feature; read by the Rule Engine for future recommendation adjustment (Rule Engine Rules 5, 7, 8 — Appendix B). |

### 3.3 Communications Interfaces

The web client and application server shall communicate over HTTPS using a RESTful API returning JSON payloads. All authentication tokens and session data shall be transmitted over encrypted channels only. No email, SMS, or third-party messaging integrations are required for Phase 1.

## 4. System Features

### 4.1 User Registration and Profile Management

#### 4.1.1 Description and Priority

Allows a new user to register, log in, and create/edit a profile capturing the attributes used by the rule engine. Priority: High.

#### 4.1.2 Stimulus/Response Sequences

- User submits registration form → System creates account and prompts for profile setup.
- User submits profile form → System validates and stores profile → System confirms save and enables meal plan generation.
- User edits an existing profile field (e.g., weekly budget) → System re-validates and stores the update, without requiring re-registration.
#### 4.1.3 Functional Requirements

REQ-4.1.1: The system shall allow a new user to register using a unique email address and password.

REQ-4.1.2: The system shall allow a registered user to log in and log out.

REQ-4.1.3: The system shall capture and store the following profile attributes: age, gender, height, weight, dietary preference, allergies, health goal, weekly budget, and cooking time available.

REQ-4.1.4: The system shall reject profile submissions with missing mandatory fields or values outside valid ranges (e.g., negative weight) and display an inline error message.

REQ-4.1.5: The system shall allow a user to edit any previously saved profile attribute at any time.

### 4.2 Weekly Meal Recommendation

#### 4.2.1 Description and Priority

Generates a 7-day meal plan (breakfast, lunch, dinner, snacks) filtered and selected according to the rule engine described in Appendix B. Priority: High.

#### 4.2.2 Stimulus/Response Sequences

- User requests a weekly meal plan → System applies diet, allergy, budget, cooking-time, variety, and nutritional-balance rules → System displays a 7-day plan.
- Rule engine cannot satisfy all constraints simultaneously (e.g., budget cannot be met) → System displays a warning and the closest feasible plan.
#### 4.2.3 Functional Requirements

REQ-4.2.1: The system shall generate a meal plan covering breakfast, lunch, dinner, and snacks for each of 7 days.

REQ-4.2.2: The system shall exclude any meal that conflicts with the user's stored dietary preference (e.g., exclude non-vegetarian meals for a vegetarian user).

REQ-4.2.3: The system shall exclude any meal containing an ingredient matching a user-declared allergy.

REQ-4.2.4: The system shall filter meals by the user's health goal: prioritizing low-calorie/high-protein/low-sugar meals for Weight Loss, high-protein/higher-calorie/complex-carbohydrate meals for Muscle Gain, and nutritionally balanced meals for Maintenance.

REQ-4.2.5: The system shall exclude recipes whose preparation time exceeds the user's stated available cooking time.

REQ-4.2.6: The system shall avoid repeating the same meal more than twice within a single 7-day plan.

REQ-4.2.7: The system shall aim for an approximate weekly nutritional balance across protein, carbohydrates, healthy fats, vegetables, and fruits.

REQ-4.2.8: If no meals satisfy all filtering constraints for a given slot, the system shall display an explanatory message rather than leaving the slot silently empty.

### 4.3 Grocery List Generator

#### 4.3.1 Description and Priority

Aggregates ingredients across the generated weekly meal plan into a single, deduplicated grocery list with combined quantities. Priority: High.

#### 4.3.2 Stimulus/Response Sequences

- User views/generates the grocery list for the current weekly plan → System aggregates ingredient quantities across all 7 days and displays a single consolidated list.
#### 4.3.3 Functional Requirements

REQ-4.3.1: The system shall aggregate ingredient quantities for identical ingredients across all meals in the weekly plan (e.g., 200g + 300g chicken = 500g).

REQ-4.3.2: The system shall remove duplicate ingredient entries after aggregation.

REQ-4.3.3: The system shall regenerate the grocery list automatically whenever a meal in the weekly plan is replaced (see Section 4.5).

REQ-4.3.4: The system shall display ingredient quantities in consistent, human-readable units.

### 4.4 Feedback System

#### 4.4.1 Description and Priority

Captures user feedback per meal to inform future recommendations. Priority: Medium.

#### 4.4.2 Stimulus/Response Sequences

- User marks a meal as Like, Dislike, Skip, or Favorite → System stores the feedback event against the user and meal → Rule engine applies Rules 5, 7, and 8 (Appendix B) in future plan generations.
#### 4.4.3 Functional Requirements

REQ-4.4.1: The system shall allow a user to mark any meal in their plan as Like, Dislike, Skip, or Favorite.

REQ-4.4.2: The system shall store each feedback event with an associated user ID, meal ID, feedback type, and timestamp.

REQ-4.4.3: The system shall lower the future selection priority of a meal marked Dislike or Skip.

REQ-4.4.4: The system shall raise the future selection priority of a meal marked Like or Favorite, and prioritize nutritionally similar meals for Favorite items.

### 4.5 Meal Replacement

#### 4.5.1 Description and Priority

Allows a user to replace a single meal in their plan while preserving budget, calorie, and diet-type constraints. Priority: High.

#### 4.5.2 Stimulus/Response Sequences

- User selects Replace on a meal → System selects an alternative meal satisfying the same diet, allergy, budget, and calorie constraints as the original → System updates the plan and regenerates the grocery list.
#### 4.5.3 Functional Requirements

REQ-4.5.1: The system shall allow a user to request replacement of any single meal within their current weekly plan.

REQ-4.5.2: The replacement meal shall satisfy the same dietary preference and allergy constraints as the original meal.

REQ-4.5.3: The replacement meal shall not cause the weekly budget to be exceeded.

REQ-4.5.4: The replacement meal shall have a calorie value within an acceptable tolerance of the original meal's calorie value.

REQ-4.5.5: If no valid replacement exists, the system shall notify the user rather than substituting a constraint-violating meal.

### 4.6 Dashboard

#### 4.6.1 Description and Priority

Provides a summary view of the user's weekly plan performance. Priority: Medium.

#### 4.6.2 Stimulus/Response Sequences

- User opens the Dashboard → System displays total weekly calories, estimated spending, meal statistics, and favorite meals derived from the current plan and feedback history.
#### 4.6.3 Functional Requirements

REQ-4.6.1: The system shall display total planned calories for the current week.

REQ-4.6.2: The system shall display estimated total spending for the current week's grocery list against the user's stated weekly budget.

REQ-4.6.3: The system shall display meal statistics (e.g., counts by category, by like/dislike status).

REQ-4.6.4: The system shall display the user's favorited meals.

### 4.7 Admin Panel

#### 4.7.1 Description and Priority

Allows administrators to manage the underlying data that powers the recommendation engine. Priority: Medium.

#### 4.7.2 Stimulus/Response Sequences

- Admin creates, edits, or deletes a Food, Recipe, Nutrition Value, or Category record → System validates and persists the change → Subsequent meal plan generations reflect the updated data.
#### 4.7.3 Functional Requirements

REQ-4.7.1: The system shall restrict access to the Admin Panel to users with an Administrator role (see Section 5.3).

REQ-4.7.2: The system shall allow an administrator to create, read, update, and delete Food records.

REQ-4.7.3: The system shall allow an administrator to create, read, update, and delete Recipe records, including their ingredient lists and preparation time.

REQ-4.7.4: The system shall allow an administrator to create, read, update, and delete Nutrition Value records associated with Foods and Recipes.

REQ-4.7.5: The system shall allow an administrator to create, read, update, and delete meal Category records.

## 5. Other Nonfunctional Requirements

### 5.1 Performance Requirements

- The system shall generate a full 7-day meal plan within 5 seconds under normal load, given a populated Food and Recipe database.
- The system shall regenerate the grocery list within 2 seconds of a meal replacement.
- The system shall support at least 100 concurrent active users in Phase 1 without perceptible degradation (TBD — to be validated against actual expected user base; see Appendix C).
### 5.2 Safety Requirements

- The system shall never recommend a meal containing an ingredient matching a user-declared allergy, under any rule-priority conflict (this constraint overrides all others, including budget and variety rules).
- The system shall clearly label estimated nutrition values as estimates and not medical advice; users with medical dietary restrictions should be directed to consult a qualified professional.
### 5.3 Security Requirements

- The system shall require authentication (login) before allowing access to any profile, meal plan, grocery list, or dashboard data.
- The system shall enforce role-based access control, restricting Admin Panel functions to users with the Administrator role.
- The system shall store user passwords using a salted, one-way hashing algorithm; passwords shall never be stored or transmitted in plain text.
- All data in transit between client and server shall be encrypted using HTTPS/TLS.
### 5.4 Software Quality Attributes

| Attribute | Requirement |
| --- | --- |
| Usability | A first-time user shall be able to complete profile setup and view their first meal plan within 5 minutes without external help. |
| Reliability | The rule engine shall produce a deterministic, constraint-compliant plan for any valid profile input; identical inputs shall not silently produce constraint-violating outputs. |
| Maintainability | Rule engine logic (Appendix B) shall be implemented as discrete, independently testable rules to support Agile sprint-based iteration and future extension (e.g., Phase 2 LLM layer). |
| Availability | The system shall target 99% uptime during business hours (TBD — to be finalized with hosting/SLA decisions). |

### 5.5 Business Rules

- Only users with the Administrator role may create, edit, or delete Food, Recipe, Nutrition Value, or Category records.
- Hard constraints (diet type, allergies, weekly budget) shall always take precedence over soft/preference-based rules (e.g., variety, favorites) in the rule engine's decision order, per Appendix B.
- Each meal shall belong to exactly one meal category (breakfast, lunch, dinner, or snack).
## 6. Other Requirements

This SRS is treated as a living document within the project's Agile SDLC process. Features in Section 4 are expected to be decomposed into user stories and delivered incrementally across sprints; this document shall be revised at the start of each release to reflect approved backlog changes. No internationalization, legal, or database-vendor-specific requirements have been identified for Phase 1 beyond those already stated in Section 2.5.

#### Note on Phase 2 (Informational — Not In Scope for This Release)

A future release is anticipated to introduce an LLM Reasoning Layer on top of the existing rule engine, enabling natural-language interaction, meal-selection explanations, ingredient substitution suggestions, and richer long-term preference learning, while the rule engine continues to enforce non-negotiable constraints (diet, allergies, budget). This is documented here only to inform Phase 1 design decisions that should not preclude this future direction; no Phase 2 requirements are specified in this SRS.

## Appendix A: Glossary

| Term | Definition |
| --- | --- |
| Rule Engine | The deterministic IF–THEN logic component that filters and selects meals based on user profile constraints (Appendix B). |
| Health Goal | A user-selected objective — Weight Loss, Muscle Gain, or Maintenance — that influences meal filtering (REQ-4.2.4). |
| Meal Category | One of: Breakfast, Lunch, Dinner, Snack. Each meal belongs to exactly one category. |
| Grocery List | The deduplicated, quantity-aggregated list of ingredients required to prepare a user's weekly meal plan. |
| Favorite | A feedback state indicating a user wishes to see this meal, or nutritionally similar meals, recommended more often. |
| LLM Reasoning Layer | A Phase 2 (out-of-scope) component intended to sit atop the rule engine to add conversational and explanatory capability. |

## Appendix B: Analysis Models

### B.1 Functional Flow

Register → Create Profile → Select Preferences → Generate Weekly Meal Plan → Generate Grocery List → User Feedback → Improve Future Recommendations.

### B.2 Business Logic Pipeline

- Step 1: Collect user information (age, gender, weight, height, activity level, health goal, diet preference, allergies, budget, cooking time).
- Step 2: Filter meals violating diet, allergy, budget, cooking time, or ingredient availability.
- Step 3: Apply health-goal-based filtering (Weight Loss / Muscle Gain / Maintenance).
- Step 4: Check total plan cost against weekly budget; replace highest-cost meals first if exceeded.
- Step 5: Remove recipes exceeding available cooking time.
- Step 6: Enforce meal variety across the week.
- Step 7: Balance weekly nutrition (protein, carbs, fats, vegetables, fruits).
- Step 8: Generate the aggregated grocery list.
- Step 9: Store user feedback (like, dislike, favorite, skipped).
- Step 10: Adjust future recommendation priority based on stored feedback.
### B.3 Rule Engine (Phase 1)

| Rule | Condition (IF) | Action (THEN) |
| --- | --- | --- |
| Rule 1 | Diet = Vegetarian | Only vegetarian meals are eligible for selection. |
| Rule 2 | Goal = Weight Loss | Calories < target threshold; Protein > minimum threshold. |
| Rule 3 | Budget exceeded | Replace highest-cost meals first. |
| Rule 4 | Cooking Time = N minutes | Only recipes with time ≤ N minutes are eligible. |
| Rule 5 | Meal disliked | Decrease the meal's future recommendation priority. |
| Rule 6 | Allergy = X | Exclude all meals containing ingredient X. |
| Rule 7 | Meal repeated > 2 times/week | Replace with a nutritionally similar alternative. |
| Rule 8 | Meal marked Favorite | Recommend nutritionally similar meals. |

## Appendix C: To Be Determined List

| # | TBD Item | Section Reference |
| --- | --- | --- |
| TBD-1 | Specific hosting provider, server OS, and database engine. | 2.4 |
| TBD-2 | Delivery format for user documentation (in-app, help center, or PDF). | 2.6 |
| TBD-3 | Concurrent user target beyond the initial 100-user estimate. | 5.1 |
| TBD-4 | Target uptime SLA and hosting agreement details. | 5.4 |
| TBD-5 | Formal specification of Phase 2 LLM Reasoning Layer requirements (out of scope for this SRS). | 2.7 |
