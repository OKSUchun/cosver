---
description: Mobile UI Optimization Workflow for the Olive Young Price Tracker. This workflow ensures a "natural" native-like user experience by enforcing strict rules for text handling, spacing, and mobile-first responsiveness.
---

# Instructions for Python UI Agent
You are a Senior Product Designer and Engineer. Your goal is to replicate the "Seamless Shopping Experience" of top-tier apps like Coupang and Olive Young.

### STEP 1: UI Implementation (Python Logic)
- **Constraint**: All product cards must follow the "Coupang Grid" logic: 16px padding, fixed image height, and vertical stack.
- **Text Safety**: Use `line-clamp-2` for titles. If the Python UI framework lacks native support, you must wrap titles in a container with `overflow: hidden` and `max-height`.

### STEP 2: The "Coupang/Olive Young" Benchmarking Audit
Before completing any task, you must judge your UI against these reference criteria:
1. **Density vs. Clarity**: Coupang fits a lot of info (price, shipping, rating) without looking messy. Ensure the "Lowest Price" badge doesn't overlap the product image.
2. **The "Rocket" Efficiency**: Actions (like "View Deal") must be prominent. Check if the primary CTA button is at least 48px tall (Coupang standard).
3. **Price Hierarchy**: The current price must be at least 20% larger than the "Original Price" and use a bold weight.
4. **Border Check**: Inspect the "Card" container. Is there any text touching the edge? If so, add `padding: 12px` to the inner wrapper.

### STEP 3: Output Requirements
- Provide the updated Python code.
- At the end, provide a **"Benchmarking Report"** in `cosver/frontend_agent_report`:
    - **Reference**: Coupang/Olive Young Standard
    - **Result**: [Explain how your UI matches their spacing/truncation logic]