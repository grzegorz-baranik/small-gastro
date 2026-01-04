# Interview Skill

This skill conducts structured requirements clarification interviews using the AskUserQuestion tool. It is **MANDATORY** for all agents before entering plan mode or making implementation decisions when requirements are unclear.

## CRITICAL: When to Use This Skill

**ALL agents MUST invoke `/interview` when:**

1. **Vague Requirements** - User request lacks specific details
2. **Multiple Valid Approaches** - More than one reasonable implementation path exists
3. **Technical Decisions** - Architecture, library, or pattern choices needed
4. **Functional Ambiguity** - Business logic or user flow unclear
5. **A/B Decision Points** - Trade-offs between options need user input
6. **Specification Creation** - Before writing any spec document
7. **Before Plan Mode** - Always clarify before planning implementation

**NEVER assume. ALWAYS ask using structured questions.**

---

## Interview Protocol

### Rule 1: Use AskUserQuestion for EVERY Question

Every clarification MUST use the `AskUserQuestion` tool with:
- 2-4 clear, distinct options
- Brief descriptions explaining each option
- Appropriate `multiSelect` setting (true for checkboxes, false for radio)
- User can always select "Other" for custom input

### Rule 2: One Question at a Time

Ask questions sequentially, adapting based on answers. Skip irrelevant questions.

### Rule 3: Summarize Before Proceeding

After gathering answers, present a clear summary for confirmation before moving to planning or implementation.

---

## Question Categories by Agent Type

### For All Agents (General Clarification)

**Scope & Priority:**
```
Question: "What is the scope of this change?"
Header: "Scope"
Options:
  - label: "Small (1-2 files)"
    description: "Minor change in existing code"
  - label: "Medium (3-5 files)"
    description: "New functionality or larger modification"
  - label: "Large (6+ files)"
    description: "Significant architectural change"
  - label: "Not sure yet"
    description: "Requires further analysis"
multiSelect: false
```

**Priority:**
```
Question: "What is the priority of this change?"
Header: "Priority"
Options:
  - label: "Critical"
    description: "Blocks other work or production"
  - label: "High"
    description: "Needed soon"
  - label: "Medium"
    description: "Scheduled for implementation"
  - label: "Low"
    description: "Nice to have, not urgent"
multiSelect: false
```

### For requirements-analyst Agent

**Feature Type:**
```
Question: "What type of feature is this?"
Header: "Type"
Options:
  - label: "New functionality"
    description: "Completely new capability in the system"
  - label: "Extension of existing"
    description: "Addition to an already working feature"
  - label: "Bug fix"
    description: "Correction of incorrect behavior"
  - label: "Refactoring"
    description: "Code improvement without behavior change"
multiSelect: false
```

**User Personas:**
```
Question: "Who will use this functionality?"
Header: "Users"
Options:
  - label: "Owner/Manager"
    description: "Person managing the establishment"
  - label: "Employee"
    description: "Person serving customers"
  - label: "Automated system"
    description: "Tasks performed automatically"
  - label: "Multiple users"
    description: "Different roles with different access"
multiSelect: true
```

**Success Criteria:**
```
Question: "How will we know the functionality works correctly?"
Header: "Criteria"
Options:
  - label: "Specific result/output"
    description: "System returns specific data"
  - label: "State change"
    description: "Data in the system changes"
  - label: "User notification"
    description: "User receives feedback"
  - label: "Performance metric"
    description: "Measurable improvement (time, quantity, etc.)"
multiSelect: true
```

### For database-architect Agent

**Schema Changes:**
```
Question: "What database changes are needed?"
Header: "Schema"
Options:
  - label: "New table"
    description: "Creating a new entity"
  - label: "Modify existing"
    description: "Adding/changing columns"
  - label: "New relations"
    description: "Connections between tables"
  - label: "No changes"
    description: "Current schema is sufficient"
multiSelect: true
```

**Data Migration:**
```
Question: "Does existing data require migration?"
Header: "Migration"
Options:
  - label: "Yes, with transformation"
    description: "Data must be transformed"
  - label: "Yes, simple transfer"
    description: "Data only moved"
  - label: "No, new data only"
    description: "Feature only applies to new records"
  - label: "To be determined"
    description: "Requires analysis of existing data"
multiSelect: false
```

### For fastapi-backend-architect Agent

**API Design:**
```
Question: "What API endpoints are needed?"
Header: "API"
Options:
  - label: "CRUD (Create/Read/Update/Delete)"
    description: "Full set of operations on a resource"
  - label: "Read only"
    description: "GET endpoints"
  - label: "Action/Operation"
    description: "POST endpoint performing an action"
  - label: "External integration"
    description: "Connection to external API"
multiSelect: true
```

**Authentication:**
```
Question: "What authorization requirements?"
Header: "Auth"
Options:
  - label: "Public endpoint"
    description: "Accessible without login"
  - label: "Logged-in user"
    description: "Requires active session"
  - label: "Specific role"
    description: "Only for admin/manager/etc."
  - label: "Resource owner"
    description: "Only for creator/owner of data"
multiSelect: false
```

### For react-frontend-architect Agent

**UI Components:**
```
Question: "What UI components are needed?"
Header: "Components"
Options:
  - label: "New page"
    description: "Completely new view"
  - label: "Modal/Dialog"
    description: "Modal window"
  - label: "Form"
    description: "Data input"
  - label: "List/Table"
    description: "Displaying multiple elements"
multiSelect: true
```

**State Management:**
```
Question: "How to manage state for this feature?"
Header: "State"
Options:
  - label: "Local (useState)"
    description: "State only in component"
  - label: "Context"
    description: "State shared between components"
  - label: "React Query"
    description: "Server state with cache"
  - label: "To be determined"
    description: "Requires requirements analysis"
multiSelect: false
```

### For testing-engineer Agent

**Test Scope:**
```
Question: "What test scope is needed?"
Header: "Tests"
Options:
  - label: "Unit tests"
    description: "Isolated function/component tests"
  - label: "Integration tests"
    description: "Tests of module cooperation"
  - label: "E2E tests"
    description: "Tests of entire user flow"
  - label: "All levels"
    description: "Full test pyramid"
multiSelect: true
```

**Test Data:**
```
Question: "What test data is needed?"
Header: "Data"
Options:
  - label: "New builders"
    description: "New test data factories"
  - label: "Existing builders"
    description: "Use existing factories"
  - label: "Fixtures from files"
    description: "Data from JSON/CSV"
  - label: "Property-based"
    description: "Generated by Hypothesis"
multiSelect: true
```

### For deployment-engineer Agent

**Deployment Target:**
```
Question: "Where to deploy this change?"
Header: "Environment"
Options:
  - label: "Local Docker only"
    description: "Local testing"
  - label: "VPS staging"
    description: "Test environment on server"
  - label: "VPS production"
    description: "Production environment"
  - label: "All environments"
    description: "Full CI/CD pipeline"
multiSelect: true
```

---

## A/B Decision Template

When multiple valid approaches exist:

```
Question: "Which approach do you prefer for [specific problem]?"
Header: "Approach"
Options:
  - label: "Option A: [name]"
    description: "[Pros and cons of option A]"
  - label: "Option B: [name]"
    description: "[Pros and cons of option B]"
  - label: "Option C: [name]" (optional)
    description: "[Pros and cons of option C]"
  - label: "I need more information"
    description: "Explain details of each option"
multiSelect: false
```

---

## Trade-off Questions

When implementation involves trade-offs:

```
Question: "What is most important for this functionality?"
Header: "Priority"
Options:
  - label: "Implementation speed"
    description: "Working solution as quickly as possible"
  - label: "Performance"
    description: "Optimal operation under load"
  - label: "Maintainability"
    description: "Clean code, easy future changes"
  - label: "User experience"
    description: "Best ergonomics and UX"
multiSelect: false
```

---

## Interview Output Format

After completing the interview, summarize:

```markdown
## Interview Summary

### Findings:
- **Scope**: [answer]
- **Priority**: [answer]
- **Type**: [answer]
- [other key findings]

### Technical Decisions:
- [decision 1]
- [decision 2]

### Identified Risks:
- [risk 1, if any]

### Next Steps:
1. [step 1]
2. [step 2]

Is the above summary correct? If so, I'll proceed to [planning/implementation].
```

---

## Language

Conduct the interview in English. For UI-facing elements that will be shown to end users in the application, use Polish (the project's primary UI language).
