# Rule: Documentation Creation Standards

This document outlines the strict rules for creating documentation within the project, specifically for Context Detail Documents and Algorithm Specifications. These rules are designed to ensure clarity, consistency, and correctness for AI-assisted development.

## 1. Context Detail Document Structure

All context detail documents MUST follow a structured Markdown format.

### Required Sections

1. **Overview**: Brief description of the module or feature.
2. **Input/Output Specifications**:
   - Explicitly define input data and their types.
   - Explicitly define output data and their types.
3. **Pseudo-code**:
   - Define behavior using pseudo-code to capture logical flow without being tied to specific syntax.
4. **Constraints**:
   - **Tech Stack**: Explicitly state relevant technologies.
   - **Core Goals**: What must be achieved?
   - **Philosophy**: Design principles.
   - **Requirements**: Functional and non-functional requirements.

### Diagramming (Mermaid)

Use Mermaid diagrams to visualize scenarios. Do not just diagram the structure; diagram the behavior.

- **Happy Path**: The ideal flow of execution.
- **Edge Cases**: Flows for boundary conditions.
- **Exception Strategies**: How errors are handled and where the flow is redirected.

## 2. Algorithm Design Specifications

When documenting algorithms, you MUST include a "Blueprint" section that includes mathematical and logical rigor.

### Mathematical Modeling & Invariants

- **Mathematical Modeling**: Represent complex business logic with mathematical formulas where possible.
- **Invariants (Absolute Rules)**:
  - Define never-changing rules.
  - Define state invariants: conditions that must be true at specific checkpoints.
  - Use mathematical constraints to reduce ambiguity and AI logic errors.

### Atomic Steps & Data Flow

- **Atomic Steps**: Break down the algorithm into the smallest logical units and number them sequentially.
- **Data Flow Visualization**: Use Mermaid sequence or flowchart diagrams to show how data transforms through these steps.

## 3. Pre-Implementation Verification

Before writing any code based on these documents, you MUST perform a logic check.

**Mandatory Prompt for AI**:
> "Based on the above specification, before implementing the algorithm, please point out any logical contradictions or expected performance bottlenecks. Also, suggest at least 3 edge cases that I might have missed."
