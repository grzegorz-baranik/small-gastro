# ADR-{NNN}: {Architecture Decision Title}

## Metadata

| Field | Value |
|-------|-------|
| **Status** | Proposed / Accepted / Rejected / Deprecated |
| **Date** | {YYYY-MM-DD} |
| **Author** | {author} |
| **Decision Makers** | {list of decision makers} |
| **Related ADR** | [ADR-XXX](./ADR-XXX-name.md) |
| **Related Feature** | [Link to spec](../specs/{feature}/README.md) |

---

## Context

### Problem
{Describe the problem or need that requires an architectural decision.}

### Background
{Provide additional context:
- Current system state
- Technical constraints
- Business requirements
- Time or resource pressure}

### Requirements
- {Requirement 1}
- {Requirement 2}
- {Requirement 3}

### Constraints
- {Constraint 1}
- {Constraint 2}

---

## Considered Options

### Option 1: {Option Name}

**Description:**
{Detailed solution description}

**Pros:**
- {Pro 1}
- {Pro 2}

**Cons:**
- {Con 1}
- {Con 2}

**Estimated Implementation Cost:**
- Effort: {low/medium/high}
- Risk: {low/medium/high}

---

### Option 2: {Option Name}

**Description:**
{Detailed solution description}

**Pros:**
- {Pro 1}
- {Pro 2}

**Cons:**
- {Con 1}
- {Con 2}

**Estimated Implementation Cost:**
- Effort: {low/medium/high}
- Risk: {low/medium/high}

---

### Option 3: {Option Name} (optional)

**Description:**
{Detailed solution description}

**Pros:**
- {Pro 1}
- {Pro 2}

**Cons:**
- {Con 1}
- {Con 2}

---

## Option Comparison

| Criterion | Option 1 | Option 2 | Option 3 |
|-----------|----------|----------|----------|
| Implementation complexity | {+/-} | {+/-} | {+/-} |
| Scalability | {+/-} | {+/-} | {+/-} |
| Performance | {+/-} | {+/-} | {+/-} |
| Maintainability | {+/-} | {+/-} | {+/-} |
| Alignment with existing architecture | {+/-} | {+/-} | {+/-} |
| Cost | {+/-} | {+/-} | {+/-} |

**Legend:** + (favorable), - (unfavorable), 0 (neutral)

---

## Decision

**Selected Option:** Option {X} - {Name}

### Justification
{Explain why this option was selected:
- Which pros were decisive?
- How do you handle the cons?
- What factors determined the choice?}

---

## Consequences

### Positive
- {Positive consequence 1}
- {Positive consequence 2}

### Negative
- {Negative consequence 1}
- {Negative consequence 2}

### Neutral
- {Neutral consequence}

---

## Implementation Plan

### Steps
1. {Step 1}
2. {Step 2}
3. {Step 3}

### Code Changes
- `{path/to/file1}` - {change description}
- `{path/to/file2}` - {change description}

### Data Migration
{Migration description if required, or "Not applicable"}

### Tests
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance tests

---

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| {Risk 1} | Low/Medium/High | Low/Medium/High | {Mitigation approach} |
| {Risk 2} | Low/Medium/High | Low/Medium/High | {Mitigation approach} |

---

## Rejected Alternatives

### {Rejected Alternative Name}
**Reason for rejection:** {Why this option was rejected}

---

## Related Documents

- [Functional Specification](../specs/{feature}/README.md)
- [Technical Specification](../specs/{feature}/TECHNICAL.md)
- [ADR-{XXX}](./ADR-XXX-name.md) - related decision

---

## Notes

{Additional notes, comments, or information that may be useful in the future}

---

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {date} | {author} | Initial version |
| 1.1 | {date} | {author} | {Change description} |

---

## Review and Update

**Last Review Date:** {YYYY-MM-DD}
**Next Review:** {YYYY-MM-DD}

This decision should be reviewed:
- [ ] When significant architecture changes occur
- [ ] When dependencies are updated
- [ ] Every {X} months
