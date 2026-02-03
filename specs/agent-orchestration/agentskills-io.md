What are skills? - Agent Skills
  URL: https://agentskills.io/what-are-skills
  The following frontmatter is required at the top of SKILL.md: name: A short identifier description: When to use this skill The Markdown body contains the actual instructions and has no specific restrictions on structure or content. This simple format has some key advantages: Self-documenting: A skill author or user can read a SKILL.md and understand what it does, making skills easy to audit ...

  --- Content ---
  [Skip to main content](https://agentskills.io/what-are-skills#content-area)
  
  [Agent Skills home page\
  \
  Agent Skills](https://agentskills.io/)
  
  Search...
  
  Ctrl KAsk AI
  
  Search...
  
  Navigation
  
  What are skills?
  
  On this page
  
  *   [How skills work](https://agentskills.io/what-are-skills#how-skills-work)
      
  *   [The SKILL.md file](https://agentskills.io/what-are-skills#the-skill-md-file)
      
  *   [Next steps](https://agentskills.io/what-are-skills#next-steps)
      
  
  At its core, a skill is a folder containing a `SKILL.md` file. This file includes metadata (`name` and `description`, at minimum) and instructions that tell an agent how to perform a specific task. Skills can also bundle scripts, templates, and reference materials.
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      my-skill/
      ├── SKILL.md          # Required: instructions + metadata
      ├── scripts/          # Optional: executable code
      ├── references/       # Optional: documentation
      └── assets/           # Optional: templates, resources
      
  
  [​](https://agentskills.io/what-are-skills#how-skills-work)
  
  How skills work
  ------------------------------------------------------------------------------
  
  Skills use **progressive disclosure** to manage context efficiently:
  
  1.  **Discovery**: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.
  2.  **Activation**: When a task matches a skill’s description, the agent reads the full `SKILL.md` instructions into context.
  3.  **Execution**: The agent follows the instructions, optionally loading referenced files or executing bundled code as needed.
  
  This approach keeps agents fast while giving them access to more context on demand.
  
  [​](https://agentskills.io/what-are-skills#the-skill-md-file)
  
  The SKILL.md file
  ----------------------------------------------------------------------------------
  
  Every skill starts with a `SKILL.md` file containing YAML frontmatter and Markdown instructions:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      ---
      name: pdf-processing
      description: Extract text and tables from PDF files, fill forms, merge documents.
      ---
      
      # PDF Processing
      
      ## When to use this skill
      Use this skill when the user needs to work with PDF files...
      
      ## How to extract text
      1. Use pdfplumber for text extraction...
      
      ## How to fill forms
      ...
      
  
  The following frontmatter is required at the top of `SKILL.md`:
  
  *   `name`: A short identifier
  *   `description`: When to use this skill
  
  The Markdown body contains the actual instructions and has no specific restrictions on structure or content. This simple format has some key advantages:
  
  *   **Self-documenting**: A skill author or user can read a `SKILL.md` and understand what it does, making skills easy to audit and improve.
  *   **Extensible**: Skills can range in complexity from just text instructions to executable code, assets, and templates.
  *   **Portable**: Skills are just files, so they’re easy to edit, version, and share.
  
  [​](https://agentskills.io/what-are-skills#next-steps)
  
  Next steps
  --------------------------------------------------------------------
  
  *   [View the specification](https://agentskills.io/specification)
       to understand the full format.
  *   [Add skills support to your agent](https://agentskills.io/integrate-skills)
       to build a compatible client.
  *   [See example skills](https://github.com/anthropics/skills)
       on GitHub.
  *   [Read authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
       for writing effective skills.
  *   [Use the reference library](https://github.com/agentskills/agentskills/tree/main/skills-ref)
       to validate skills and generate prompt XML.
  
  [Overview](https://agentskills.io/home)
  [Specification](https://agentskills.io/specification)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

Specification - Agent Skills
  URL: https://agentskills.io/specification
  The complete format specification for Agent Skills. Body content The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions. Write whatever helps agents perform the task effectively. Recommended sections: Step-by-step instructions Examples of inputs and outputs Common edge cases Note that the agent will load this entire file once it's decided to ...

  --- Content ---
  [Skip to main content](https://agentskills.io/specification#content-area)
  
  [Agent Skills home page\
  \
  Agent Skills](https://agentskills.io/)
  
  Search...
  
  Ctrl KAsk AI
  
  Search...
  
  Navigation
  
  Specification
  
  On this page
  
  *   [Directory structure](https://agentskills.io/specification#directory-structure)
      
  *   [SKILL.md format](https://agentskills.io/specification#skill-md-format)
      
  *   [Frontmatter (required)](https://agentskills.io/specification#frontmatter-required)
      
  *   [name field](https://agentskills.io/specification#name-field)
      
  *   [description field](https://agentskills.io/specification#description-field)
      
  *   [license field](https://agentskills.io/specification#license-field)
      
  *   [compatibility field](https://agentskills.io/specification#compatibility-field)
      
  *   [metadata field](https://agentskills.io/specification#metadata-field)
      
  *   [allowed-tools field](https://agentskills.io/specification#allowed-tools-field)
      
  *   [Body content](https://agentskills.io/specification#body-content)
      
  *   [Optional directories](https://agentskills.io/specification#optional-directories)
      
  *   [scripts/](https://agentskills.io/specification#scripts%2F)
      
  *   [references/](https://agentskills.io/specification#references%2F)
      
  *   [assets/](https://agentskills.io/specification#assets%2F)
      
  *   [Progressive disclosure](https://agentskills.io/specification#progressive-disclosure)
      
  *   [File references](https://agentskills.io/specification#file-references)
      
  *   [Validation](https://agentskills.io/specification#validation)
      
  
  This document defines the Agent Skills format.
  
  [​](https://agentskills.io/specification#directory-structure)
  
  Directory structure
  ------------------------------------------------------------------------------------
  
  A skill is a directory containing at minimum a `SKILL.md` file:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      skill-name/
      └── SKILL.md          # Required
      
  
  You can optionally include [additional directories](https://agentskills.io/specification#optional-directories)
   such as `scripts/`, `references/`, and `assets/` to support your skill.
  
  [​](https://agentskills.io/specification#skill-md-format)
  
  SKILL.md format
  ----------------------------------------------------------------------------
  
  The `SKILL.md` file must contain YAML frontmatter followed by Markdown content.
  
  ### 
  
  [​](https://agentskills.io/specification#frontmatter-required)
  
  Frontmatter (required)
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      ---
      name: skill-name
      description: A description of what this skill does and when to use it.
      ---
      
  
  With optional fields:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      ---
      name: pdf-processing
      description: Extract text and tables from PDF files, fill forms, merge documents.
      license: Apache-2.0
      metadata:
        author: example-org
        version: "1.0"
      ---
      
  
  | Field | Required | Constraints |
  | --- | --- | --- |
  | `name` | Yes | Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen. |
  | `description` | Yes | Max 1024 characters. Non-empty. Describes what the skill does and when to use it. |
  | `license` | No  | License name or reference to a bundled license file. |
  | `compatibility` | No  | Max 500 characters. Indicates environment requirements (intended product, system packages, network access, etc.). |
  | `metadata` | No  | Arbitrary key-value mapping for additional metadata. |
  | `allowed-tools` | No  | Space-delimited list of pre-approved tools the skill may use. (Experimental) |
  
  #### 
  
  [​](https://agentskills.io/specification#name-field)
  
  `name` field
  
  The required `name` field:
  
  *   Must be 1-64 characters
  *   May only contain unicode lowercase alphanumeric characters and hyphens (`a-z` and `-`)
  *   Must not start or end with `-`
  *   Must not contain consecutive hyphens (`--`)
  *   Must match the parent directory name
  
  Valid examples:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: pdf-processing
      
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: data-analysis
      
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: code-review
      
  
  Invalid examples:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: PDF-Processing  # uppercase not allowed
      
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: -pdf  # cannot start with hyphen
      
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      name: pdf--processing  # consecutive hyphens not allowed
      
  
  #### 
  
  [​](https://agentskills.io/specification#description-field)
  
  `description` field
  
  The required `description` field:
  
  *   Must be 1-1024 characters
  *   Should describe both what the skill does and when to use it
  *   Should include specific keywords that help agents identify relevant tasks
  
  Good example:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
      
  
  Poor example:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      description: Helps with PDFs.
      
  
  #### 
  
  [​](https://agentskills.io/specification#license-field)
  
  `license` field
  
  The optional `license` field:
  
  *   Specifies the license applied to the skill
  *   We recommend keeping it short (either the name of a license or the name of a bundled license file)
  
  Example:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      license: Proprietary. LICENSE.txt has complete terms
      
  
  #### 
  
  [​](https://agentskills.io/specification#compatibility-field)
  
  `compatibility` field
  
  The optional `compatibility` field:
  
  *   Must be 1-500 characters if provided
  *   Should only be included if your skill has specific environment requirements
  *   Can indicate intended product, required system packages, network access needs, etc.
  
  Examples:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      compatibility: Designed for Claude Code (or similar products)
      
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      compatibility: Requires git, docker, jq, and access to the internet
      
  
  Most skills do not need the `compatibility` field.
  
  #### 
  
  [​](https://agentskills.io/specification#metadata-field)
  
  `metadata` field
  
  The optional `metadata` field:
  
  *   A map from string keys to string values
  *   Clients can use this to store additional properties not defined by the Agent Skills spec
  *   We recommend making your key names reasonably unique to avoid accidental conflicts
  
  Example:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      metadata:
        author: example-org
        version: "1.0"
      
  
  #### 
  
  [​](https://agentskills.io/specification#allowed-tools-field)
  
  `allowed-tools` field
  
  The optional `allowed-tools` field:
  
  *   A space-delimited list of tools that are pre-approved to run
  *   Experimental. Support for this field may vary between agent implementations
  
  Example:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      allowed-tools: Bash(git:*) Bash(jq:*) Read
      
  
  ### 
  
  [​](https://agentskills.io/specification#body-content)
  
  Body content
  
  The Markdown body after the frontmatter contains the skill instructions. There are no format restrictions. Write whatever helps agents perform the task effectively. Recommended sections:
  
  *   Step-by-step instructions
  *   Examples of inputs and outputs
  *   Common edge cases
  
  Note that the agent will load this entire file once it’s decided to activate a skill. Consider splitting longer `SKILL.md` content into referenced files.
  
  [​](https://agentskills.io/specification#optional-directories)
  
  Optional directories
  --------------------------------------------------------------------------------------
  
  ### 
  
  [​](https://agentskills.io/specification#scripts/)
  
  scripts/
  
  Contains executable code that agents can run. Scripts should:
  
  *   Be self-contained or clearly document dependencies
  *   Include helpful error messages
  *   Handle edge cases gracefully
  
  Supported languages depend on the agent implementation. Common options include Python, Bash, and JavaScript.
  
  ### 
  
  [​](https://agentskills.io/specification#references/)
  
  references/
  
  Contains additional documentation that agents can read when needed:
  
  *   `REFERENCE.md` - Detailed technical reference
  *   `FORMS.md` - Form templates or structured data formats
  *   Domain-specific files (`finance.md`, `legal.md`, etc.)
  
  Keep individual [reference files](https://agentskills.io/specification#file-references)
   focused. Agents load these on demand, so smaller files mean less use of context.
  
  ### 
  
  [​](https://agentskills.io/specification#assets/)
  
  assets/
  
  Contains static resources:
  
  *   Templates (document templates, configuration templates)
  *   Images (diagrams, examples)
  *   Data files (lookup tables, schemas)
  
  [​](https://agentskills.io/specification#progressive-disclosure)
  
  Progressive disclosure
  ------------------------------------------------------------------------------------------
  
  Skills should be structured for efficient use of context:
  
  1.  **Metadata** (~100 tokens): The `name` and `description` fields are loaded at startup for all skills
  2.  **Instructions** (< 5000 tokens recommended): The full `SKILL.md` body is loaded when the skill is activated
  3.  **Resources** (as needed): Files (e.g. those in `scripts/`, `references/`, or `assets/`) are loaded only when required
  
  Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files.
  
  [​](https://agentskills.io/specification#file-references)
  
  File references
  ----------------------------------------------------------------------------
  
  When referencing other files in your skill, use relative paths from the skill root:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      See [the reference guide](references/REFERENCE.md) for details.
      
      Run the extraction script:
      scripts/extract.py
      
  
  Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.
  
  [​](https://agentskills.io/specification#validation)
  
  Validation
  ------------------------------------------------------------------
  
  Use the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)
   reference library to validate your skills:
  
  Report incorrect code
  
  Copy
  
  Ask AI
  
      skills-ref validate ./my-skill
      
  
  This checks that your `SKILL.md` frontmatter is valid and follows all naming conventions.
  
  [What are skills?](https://agentskills.io/what-are-skills)
  [Integrate skills](https://agentskills.io/integrate-skills)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---

Overview - Agent Skills
  URL: https://agentskills.io/home
  A simple, open format for giving agents new capabilities and expertise. Agent Skills are folders of instructions, scripts, and resources that agents can discover and use to do things more accurately and efficiently.

  --- Content ---
  [Skip to main content](https://agentskills.io/home#content-area)
  
  [Agent Skills home page\
  \
  Agent Skills](https://agentskills.io/)
  
  Search...
  
  Ctrl KAsk AI
  
  Search...
  
  Navigation
  
  Overview
  
  On this page
  
  *   [Why Agent Skills?](https://agentskills.io/home#why-agent-skills)
      
  *   [What can Agent Skills enable?](https://agentskills.io/home#what-can-agent-skills-enable)
      
  *   [Adoption](https://agentskills.io/home#adoption)
      
  *   [Open development](https://agentskills.io/home#open-development)
      
  *   [Get started](https://agentskills.io/home#get-started)
      
  
  Agent Skills are folders of instructions, scripts, and resources that agents can discover and use to do things more accurately and efficiently.
  
  [​](https://agentskills.io/home#why-agent-skills)
  
  Why Agent Skills?
  ----------------------------------------------------------------------
  
  Agents are increasingly capable, but often don’t have the context they need to do real work reliably. Skills solve this by giving agents access to procedural knowledge and company-, team-, and user-specific context they can load on demand. Agents with access to a set of skills can extend their capabilities based on the task they’re working on. **For skill authors**: Build capabilities once and deploy them across multiple agent products. **For compatible agents**: Support for skills lets end users give agents new capabilities out of the box. **For teams and enterprises**: Capture organizational knowledge in portable, version-controlled packages.
  
  [​](https://agentskills.io/home#what-can-agent-skills-enable)
  
  What can Agent Skills enable?
  ----------------------------------------------------------------------------------------------
  
  *   **Domain expertise**: Package specialized knowledge into reusable instructions, from legal review processes to data analysis pipelines.
  *   **New capabilities**: Give agents new capabilities (e.g. creating presentations, building MCP servers, analyzing datasets).
  *   **Repeatable workflows**: Turn multi-step tasks into consistent and auditable workflows.
  *   **Interoperability**: Reuse the same skill across different skills-compatible agent products.
  
  [​](https://agentskills.io/home#adoption)
  
  Adoption
  -----------------------------------------------------
  
  Agent Skills are supported by leading AI development tools.
  
  [![Agentman](https://agentskills.io/images/logos/agentman/agentman-wordmark-light.svg)![Agentman](https://agentskills.io/images/logos/agentman/agentman-wordmark-dark.svg)](https://agentman.ai/)
  [![GitHub](https://agentskills.io/images/logos/github/GitHub_Lockup_Dark.svg)![GitHub](https://agentskills.io/images/logos/github/GitHub_Lockup_Light.svg)](https://github.com/)
  [![Command Code](https://agentskills.io/images/logos/command-code/command-code-logo-for-light.svg)![Command Code](https://agentskills.io/images/logos/command-code/command-code-logo-for-dark.svg)](https://commandcode.ai/)
  [![pi](https://agentskills.io/images/logos/pi/pi-logo-light.svg)![pi](https://agentskills.io/images/logos/pi/pi-logo-dark.svg)](https://shittycodingagent.ai/)
  [![Goose](https://agentskills.io/images/logos/goose/goose-logo-black.png)![Goose](https://agentskills.io/images/logos/goose/goose-logo-white.png)](https://block.github.io/goose/)
  [![VS Code](https://agentskills.io/images/logos/vscode/vscode.svg)![VS Code](https://agentskills.io/images/logos/vscode/vscode-alt.svg)](https://code.visualstudio.com/)
  [![Factory](https://agentskills.io/images/logos/factory/factory-logo-light.svg)![Factory](https://agentskills.io/images/logos/factory/factory-logo-dark.svg)](https://factory.ai/)
  [![Claude](https://agentskills.io/images/logos/claude-ai/Claude-logo-Slate.svg)![Claude](https://agentskills.io/images/logos/claude-ai/Claude-logo-Ivory.svg)](https://claude.ai/)
  [![Spring AI](https://agentskills.io/images/logos/spring-ai/spring-ai-logo-light.svg)![Spring AI](https://agentskills.io/images/logos/spring-ai/spring-ai-logo-dark.svg)](https://docs.spring.io/spring-ai/reference)
  [![TRAE](https://agentskills.io/images/logos/trae/trae-logo-lightmode.svg)![TRAE](https://agentskills.io/images/logos/trae/trae-logo-darkmode.svg)](https://trae.ai/)
  [![OpenAI Codex](https://agentskills.io/images/logos/oai-codex/OAI_Codex-Lockup_400px.svg)![OpenAI Codex](https://agentskills.io/images/logos/oai-codex/OAI_Codex-Lockup_400px_Darkmode.svg)](https://developers.openai.com/codex)
  [![Gemini CLI](https://agentskills.io/images/logos/gemini-cli/gemini-cli-logo_light.svg)![Gemini CLI](https://agentskills.io/images/logos/gemini-cli/gemini-cli-logo_dark.svg)](https://geminicli.com/)
  [![OpenCode](https://agentskills.io/images/logos/opencode/opencode-wordmark-light.svg)![OpenCode](https://agentskills.io/images/logos/opencode/opencode-wordmark-dark.svg)](https://opencode.ai/)
  [![Agentman](https://agentskills.io/images/logos/agentman/agentman-wordmark-light.svg)![Agentman](https://agentskills.io/images/logos/agentman/agentman-wordmark-dark.svg)](https://agentman.ai/)
  [![GitHub](https://agentskills.io/images/logos/github/GitHub_Lockup_Dark.svg)![GitHub](https://agentskills.io/images/logos/github/GitHub_Lockup_Light.svg)](https://github.com/)
  [![Command Code](https://agentskills.io/images/logos/command-code/command-code-logo-for-light.svg)![Command Code](https://agentskills.io/images/logos/command-code/command-code-logo-for-dark.svg)](https://commandcode.ai/)
  [![pi](https://agentskills.io/images/logos/pi/pi-logo-light.svg)![pi](https://agentskills.io/images/logos/pi/pi-logo-dark.svg)](https://shittycodingagent.ai/)
  [![Goose](https://agentskills.io/images/logos/goose/goose-logo-black.png)![Goose](https://agentskills.io/images/logos/goose/goose-logo-white.png)](https://block.github.io/goose/)
  [![VS Code](https://agentskills.io/images/logos/vscode/vscode.svg)![VS Code](https://agentskills.io/images/logos/vscode/vscode-alt.svg)](https://code.visualstudio.com/)
  [![Factory](https://agentskills.io/images/logos/factory/factory-logo-light.svg)![Factory](https://agentskills.io/images/logos/factory/factory-logo-dark.svg)](https://factory.ai/)
  [![Claude](https://agentskills.io/images/logos/claude-ai/Claude-logo-Slate.svg)![Claude](https://agentskills.io/images/logos/claude-ai/Claude-logo-Ivory.svg)](https://claude.ai/)
  [![Spring AI](https://agentskills.io/images/logos/spring-ai/spring-ai-logo-light.svg)![Spring AI](https://agentskills.io/images/logos/spring-ai/spring-ai-logo-dark.svg)](https://docs.spring.io/spring-ai/reference)
  [![TRAE](https://agentskills.io/images/logos/trae/trae-logo-lightmode.svg)![TRAE](https://agentskills.io/images/logos/trae/trae-logo-darkmode.svg)](https://trae.ai/)
  [![OpenAI Codex](https://agentskills.io/images/logos/oai-codex/OAI_Codex-Lockup_400px.svg)![OpenAI Codex](https://agentskills.io/images/logos/oai-codex/OAI_Codex-Lockup_400px_Darkmode.svg)](https://developers.openai.com/codex)
  [![Gemini CLI](https://agentskills.io/images/logos/gemini-cli/gemini-cli-logo_light.svg)![Gemini CLI](https://agentskills.io/images/logos/gemini-cli/gemini-cli-logo_dark.svg)](https://geminicli.com/)
  [![OpenCode](https://agentskills.io/images/logos/opencode/opencode-wordmark-light.svg)![OpenCode](https://agentskills.io/images/logos/opencode/opencode-wordmark-dark.svg)](https://opencode.ai/)
  
  [![Mux](https://agentskills.io/images/logos/mux/mux-editor-light.svg)![Mux](https://agentskills.io/images/logos/mux/mux-editor-dark.svg)](https://mux.coder.com/)
  [![Mistral AI Vibe](https://agentskills.io/images/logos/mistral-vibe/vibe-logo_black.svg)![Mistral AI Vibe](https://agentskills.io/images/logos/mistral-vibe/vibe-logo_white.svg)](https://github.com/mistralai/mistral-vibe)
  [![Cursor](https://agentskills.io/images/logos/cursor/LOCKUP_HORIZONTAL_2D_LIGHT.svg)![Cursor](https://agentskills.io/images/logos/cursor/LOCKUP_HORIZONTAL_2D_DARK.svg)](https://cursor.com/)
  [![Autohand Code CLI](https://agentskills.io/images/logos/autohand/autohand-light.svg)![Autohand Code CLI](https://agentskills.io/images/logos/autohand/autohand-dark.svg)](https://autohand.ai/)
  [![Databricks](https://agentskills.io/images/logos/databricks/databricks-logo-light.svg)![Databricks](https://agentskills.io/images/logos/databricks/databricks-logo-dark.svg)](https://databricks.com/)
  [![Firebender](https://agentskills.io/images/logos/firebender/firebender-wordmark-light.svg)![Firebender](https://agentskills.io/images/logos/firebender/firebender-wordmark-dark.svg)](https://firebender.com/)
  [![Claude Code](https://agentskills.io/images/logos/claude-code/Claude-Code-logo-Slate.svg)![Claude Code](https://agentskills.io/images/logos/claude-code/Claude-Code-logo-Ivory.svg)](https://claude.ai/code)
  [![Amp](https://agentskills.io/images/logos/amp/amp-logo-light.svg)![Amp](https://agentskills.io/images/logos/amp/amp-logo-dark.svg)](https://ampcode.com/)
  [![Letta](https://agentskills.io/images/logos/letta/Letta-logo-RGB_OffBlackonTransparent.svg)![Letta](https://agentskills.io/images/logos/letta/Letta-logo-RGB_GreyonTransparent.svg)](https://www.letta.com/)
  [![Roo Code](https://agentskills.io/images/logos/roo-code/roo-code-logo-black.svg)![Roo Code](https://agentskills.io/images/logos/roo-code/roo-code-logo-white.svg)](https://roocode.com/)
  [![VT Code](https://agentskills.io/images/logos/vtcode/vt_code_light.svg)![VT Code](https://agentskills.io/images/logos/vtcode/vt_code_dark.svg)](https://github.com/vinhnx/vtcode)
  [![Piebald](https://agentskills.io/images/logos/piebald/Piebald_wordmark_light.svg)![Piebald](https://agentskills.io/images/logos/piebald/Piebald_wordmark_dark.svg)](https://piebald.ai/)
  [![Ona](https://agentskills.io/images/logos/ona/ona-wordmark-light.svg)![Ona](https://agentskills.io/images/logos/ona/ona-wordmark-dark.svg)](https://ona.com/)
  [![Mux](https://agentskills.io/images/logos/mux/mux-editor-light.svg)![Mux](https://agentskills.io/images/logos/mux/mux-editor-dark.svg)](https://mux.coder.com/)
  [![Mistral AI Vibe](https://agentskills.io/images/logos/mistral-vibe/vibe-logo_black.svg)![Mistral AI Vibe](https://agentskills.io/images/logos/mistral-vibe/vibe-logo_white.svg)](https://github.com/mistralai/mistral-vibe)
  [![Cursor](https://agentskills.io/images/logos/cursor/LOCKUP_HORIZONTAL_2D_LIGHT.svg)![Cursor](https://agentskills.io/images/logos/cursor/LOCKUP_HORIZONTAL_2D_DARK.svg)](https://cursor.com/)
  [![Autohand Code CLI](https://agentskills.io/images/logos/autohand/autohand-light.svg)![Autohand Code CLI](https://agentskills.io/images/logos/autohand/autohand-dark.svg)](https://autohand.ai/)
  [![Databricks](https://agentskills.io/images/logos/databricks/databricks-logo-light.svg)![Databricks](https://agentskills.io/images/logos/databricks/databricks-logo-dark.svg)](https://databricks.com/)
  [![Firebender](https://agentskills.io/images/logos/firebender/firebender-wordmark-light.svg)![Firebender](https://agentskills.io/images/logos/firebender/firebender-wordmark-dark.svg)](https://firebender.com/)
  [![Claude Code](https://agentskills.io/images/logos/claude-code/Claude-Code-logo-Slate.svg)![Claude Code](https://agentskills.io/images/logos/claude-code/Claude-Code-logo-Ivory.svg)](https://claude.ai/code)
  [![Amp](https://agentskills.io/images/logos/amp/amp-logo-light.svg)![Amp](https://agentskills.io/images/logos/amp/amp-logo-dark.svg)](https://ampcode.com/)
  [![Letta](https://agentskills.io/images/logos/letta/Letta-logo-RGB_OffBlackonTransparent.svg)![Letta](https://agentskills.io/images/logos/letta/Letta-logo-RGB_GreyonTransparent.svg)](https://www.letta.com/)
  [![Roo Code](https://agentskills.io/images/logos/roo-code/roo-code-logo-black.svg)![Roo Code](https://agentskills.io/images/logos/roo-code/roo-code-logo-white.svg)](https://roocode.com/)
  [![VT Code](https://agentskills.io/images/logos/vtcode/vt_code_light.svg)![VT Code](https://agentskills.io/images/logos/vtcode/vt_code_dark.svg)](https://github.com/vinhnx/vtcode)
  [![Piebald](https://agentskills.io/images/logos/piebald/Piebald_wordmark_light.svg)![Piebald](https://agentskills.io/images/logos/piebald/Piebald_wordmark_dark.svg)](https://piebald.ai/)
  [![Ona](https://agentskills.io/images/logos/ona/ona-wordmark-light.svg)![Ona](https://agentskills.io/images/logos/ona/ona-wordmark-dark.svg)](https://ona.com/)
  
  [​](https://agentskills.io/home#open-development)
  
  Open development
  ---------------------------------------------------------------------
  
  The Agent Skills format was originally developed by [Anthropic](https://www.anthropic.com/)
  , released as an open standard, and has been adopted by a growing number of agent products. The standard is open to contributions from the broader ecosystem. [View on GitHub](https://github.com/agentskills/agentskills)
  
  [​](https://agentskills.io/home#get-started)
  
  Get started
  -----------------------------------------------------------
  
  [What are skills?\
  ----------------\
  \
  Learn about skills, how they work, and why they matter.](https://agentskills.io/what-are-skills)
  [Specification\
  -------------\
  \
  The complete format specification for SKILL.md files.](https://agentskills.io/specification)
  [Integrate skills\
  ----------------\
  \
  Add skills support to your agent or tool.](https://agentskills.io/integrate-skills)
  [Example skills\
  --------------\
  \
  Browse example skills on GitHub.](https://github.com/anthropics/skills)
  [Reference library\
  -----------------\
  \
  Validate skills and generate prompt XML.](https://github.com/agentskills/agentskills/tree/main/skills-ref)
  
  [What are skills?](https://agentskills.io/what-are-skills)
  
  Ctrl+I
  
  Assistant
  
  Responses are generated using AI and may contain mistakes.
  --- End Content ---
