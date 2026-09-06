We're going to implement a new feature. The user has provided a description of the feature. Your job is to plan this out.

Follow these steps:

1. Create a technical plan that describes the feature the user wants to build.
2. Research the files and functions that need to be changed to implement the feature.
3. Avoid any product manager style sections like success criteria, timelines, migration steps, etc.
4. Avoid writing any code in the plan.
5. Include specific and verbatim details from the user's prompt to ensure the plan is accurate.

The result is strictly a technical requirements document that contains the following information:

- Brief description to give context at the top.
- List of all relevant files and functions that need to be created or modified.
- Step-by-step explanation of any algorithms that are used.
- If the feature is especially large, identify phases in which the feature can be implemented.

If the user's requirements are unclear, especially after researching the relevant files, ask clarifying questions before writing the plan. Incorporate the user's answers into the plan.

Be concise and precise first. Make the plan as tight as possible without losing any critical details from the user's requirements.

Document the feature in `docs/features/<FEATURE>/plan.md`. `<FEATURE>` needs to be replaced with a concise description of the feature in snake_case with a maximum of 5 words.
