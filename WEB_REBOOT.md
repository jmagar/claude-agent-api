# apps/web Reboot (apps/web-reboot)

## Problem
Our current implementation of apps/web was created with a very faulty plan - It was supposed to use Assistant-UI for all the UI components, and instead of doing that we ended up creating ALL custom react components and not even using any Assistant-UI. The package wasnt even installed!

## Proposed Solution
I think the best, cleanest, and most sustainable path forward for the reboot is:

- AI SDK v6 - https://ai-sdk.dev/docs/introduction
- AI Elements - https://ai-sdk.dev/elements
- Streamdown - https://streamdown.ai/docs
- AI SDK Custom Provider - https://ai-sdk.dev/docs/reference/ai-sdk-core/custom-provider

We create a custom provider for AI SDK v6 that connects to our backend (apps/api). 

We use AI Elements for all UI components.

We use Streamdown instead of react-markdown to render markdown content, since it's purpose-built for the AI SDK ecosystem.

These are all parts of the same ecosystem, created and maintained by the same team.

This way we have a stack that is purposefully built to work with each other.

## Benefits
- Less code to maintain - We can remove a lot of custom code that we currently have in apps/web.
- Better UX - AI Elements are designed for AI applications, so they will provide a better user experience out of the box.
- Easier to extend - The AI SDK ecosystem is designed to be extended, so we can easily add new features in the future.
- Better performance - The AI SDK ecosystem is optimized for performance, so we can expect better performance than our current implementation.
- Future-proof - By using the latest version of the AI SDK, we ensure that our application is built on a solid foundation that will be supported and updated in the future.
- Consistency - Using components from the same ecosystem ensures a consistent look and feel across the application.
- Community Support - The AI SDK has a growing community and support from the developers, which can be beneficial for troubleshooting and getting help.
- Documentation - The AI SDK and its components are well-documented, making it easier for developers to understand and implement features.
- Integration - The AI SDK ecosystem is designed to work seamlessly together, reducing the chances of integration issues.
- With this reboot, we can create a more maintainable, user-friendly, and future-proof application that leverages the strengths of the AI SDK ecosystem.
- Swapping LLM providers becomes trivial with the custom provider architecture.