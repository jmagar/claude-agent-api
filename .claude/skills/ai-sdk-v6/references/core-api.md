# AI SDK Core API Reference

## Table of Contents

1. [Text Generation](#text-generation)
2. [Streaming Text](#streaming-text)
3. [Structured Data Generation](#structured-data-generation)
4. [Tool Calling](#tool-calling)
5. [Multi-Step Tool Execution](#multi-step-tool-execution)
6. [Embeddings & Reranking](#embeddings--reranking)
7. [Image Generation](#image-generation)
8. [Language Model Middleware](#language-model-middleware)

---

## Text Generation

### generateText

Generate text for non-interactive use cases (drafting emails, summarizing documents, agent reasoning).

```typescript
import { generateText } from 'ai';

const { text, usage, finishReason, response } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  system: 'You are a professional writer.',
  prompt: 'Summarize this article...',
});
```

**Result Properties:**
- `text` - Generated text
- `reasoning` / `reasoningText` - Model reasoning (if supported)
- `toolCalls` / `toolResults` - Tool invocations from the last step
- `finishReason` - Why generation stopped (`stop`, `length`, `tool-calls`, etc.)
- `usage` / `totalUsage` - Token consumption
- `steps` - All intermediate steps (for multi-step)
- `response.messages` - Messages for conversation history
- `sources` - Referenced sources (Perplexity, Google)

**onFinish Callback:**
```typescript
const result = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Hello',
  onFinish({ text, finishReason, usage, response, steps, totalUsage }) {
    const messages = response.messages; // for saving chat history
  },
});
```

---

## Streaming Text

### streamText

Stream text for interactive use cases (chatbots, real-time applications).

```typescript
import { streamText } from 'ai';

const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Explain machine learning.',
});

// As AsyncIterable
for await (const text of result.textStream) {
  process.stdout.write(text);
}

// As ReadableStream
const stream = result.textStream;
```

**Stream Callbacks:**
```typescript
const result = streamText({
  model: 'anthropic/claude-sonnet-4.5',
  prompt: 'Hello',
  onChunk({ chunk }) {
    if (chunk.type === 'text') console.log(chunk.text);
  },
  onFinish({ text, finishReason, usage }) {
    console.log('Done:', text);
  },
  onError({ error }) {
    console.error(error);
  },
});
```

**Full Stream Events:**
```typescript
for await (const part of result.fullStream) {
  switch (part.type) {
    case 'text-delta': console.log(part.text); break;
    case 'tool-call': console.log(part.toolName, part.input); break;
    case 'tool-result': console.log(part.result); break;
    case 'reasoning-delta': console.log(part.text); break;
    case 'source': console.log(part.url); break;
    case 'finish': console.log(part.finishReason); break;
  }
}
```

**Stream Transformation (Smoothing):**
```typescript
import { smoothStream, streamText } from 'ai';

const result = streamText({
  model,
  prompt,
  experimental_transform: smoothStream(),
});
```

**HTTP Response Helpers:**
```typescript
// For AI SDK UI integration
return result.toUIMessageStreamResponse();

// For simple text streaming
return result.toTextStreamResponse();

// Node.js response
result.pipeUIMessageStreamToResponse(res);
result.pipeTextStreamToResponse(res);
```

---

## Structured Data Generation

### generateObject

Generate type-safe structured data from LLMs.

```typescript
import { generateObject } from 'ai';
import { z } from 'zod';

const { object } = await generateObject({
  model: 'anthropic/claude-sonnet-4.5',
  schema: z.object({
    name: z.string(),
    ingredients: z.array(z.object({
      name: z.string(),
      amount: z.string(),
    })),
    steps: z.array(z.string()),
  }),
  prompt: 'Generate a lasagna recipe.',
});
```

### Output Types

```typescript
import { Output } from 'ai';

// Object output
output: Output.object({ schema: z.object({ ... }) })

// Array output
output: Output.array({ schema: z.object({ ... }) })

// Choice from options
output: Output.choice({ values: ['option1', 'option2'] })

// Raw JSON
output: Output.json()

// Plain text (default)
output: Output.text()
```

### streamObject

Stream structured data as it's being generated:

```typescript
import { streamObject } from 'ai';

const result = streamObject({
  model: 'anthropic/claude-sonnet-4.5',
  schema,
  prompt: 'Generate a recipe',
});

for await (const partialObject of result.partialObjectStream) {
  console.log(partialObject); // Partially complete object
}
```

---

## Tool Calling

### Defining Tools

```typescript
import { tool } from 'ai';
import { z } from 'zod';

const weatherTool = tool({
  description: 'Get the weather in a location',
  inputSchema: z.object({
    location: z.string().describe('City name'),
    unit: z.enum(['celsius', 'fahrenheit']).optional(),
  }),
  execute: async ({ location, unit }) => ({
    location,
    temperature: 72,
    unit: unit ?? 'fahrenheit',
  }),
});
```

**Tool Properties:**
- `description` - Helps model understand when to use the tool
- `inputSchema` - Zod/JSON schema for input validation
- `execute` - Async function called with validated inputs
- `strict` - Enable strict schema validation (provider-dependent)
- `needsApproval` - Require human approval before execution
- `inputExamples` - Example inputs to guide the model

### Using Tools

```typescript
const result = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: {
    weather: weatherTool,
    calculator: calculatorTool,
  },
  prompt: 'What is the weather in SF?',
});

console.log(result.toolCalls); // Tool calls made
console.log(result.toolResults); // Results from tool execution
```

### Tool Execution Approval

```typescript
const dangerousTool = tool({
  description: 'Execute shell command',
  inputSchema: z.object({ command: z.string() }),
  needsApproval: true, // Always require approval
  // Or dynamic:
  // needsApproval: async ({ command }) => command.includes('rm'),
  execute: async ({ command }) => { /* ... */ },
});

// Check result for approval requests
for (const part of result.content) {
  if (part.type === 'tool-approval-request') {
    // Show UI for approval
    // Then continue with tool-approval-response message
  }
}
```

### Tool Choice

```typescript
const result = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { weather, calculator },
  toolChoice: 'auto',     // Model decides (default)
  // toolChoice: 'required',  // Must call a tool
  // toolChoice: 'none',      // No tools allowed
  // toolChoice: { type: 'tool', toolName: 'weather' }, // Specific tool
  prompt: 'Calculate 2 + 2',
});
```

### Custom Tool Output for Model

Control what gets sent back to the model:

```typescript
const screenshotTool = tool({
  description: 'Take a screenshot',
  inputSchema: z.object({}),
  execute: async () => {
    const imageData = await captureScreen();
    return { type: 'image', data: imageData };
  },
  toModelOutput: ({ output }) => ({
    type: 'content',
    value: [{ type: 'media', data: output.data, mediaType: 'image/png' }],
  }),
});
```

---

## Multi-Step Tool Execution

### stopWhen Condition

Enable automatic multi-step tool execution:

```typescript
import { generateText, stepCountIs } from 'ai';

const { text, steps } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  tools: { weather, search },
  stopWhen: stepCountIs(5), // Max 5 steps
  prompt: 'Research the weather in the top 3 US cities',
});

// Access all steps
for (const step of steps) {
  console.log(step.text, step.toolCalls, step.toolResults);
}
```

### Step Callbacks

```typescript
const result = await generateText({
  // ...
  onStepFinish({ text, toolCalls, toolResults, finishReason, usage }) {
    console.log('Step completed');
  },
});
```

### prepareStep Callback

Customize settings per step:

```typescript
const result = await generateText({
  // ...
  prepareStep: async ({ stepNumber, steps, messages }) => {
    if (stepNumber === 0) {
      return {
        toolChoice: { type: 'tool', toolName: 'search' },
        activeTools: ['search'],
      };
    }
    // Compress history for longer loops
    if (messages.length > 20) {
      return { messages: messages.slice(-10) };
    }
    return {};
  },
});
```

### Response Messages

Add generated messages to conversation history:

```typescript
import { generateText, ModelMessage } from 'ai';

const messages: ModelMessage[] = [
  { role: 'user', content: 'Hello' },
];

const { response } = await generateText({
  model: 'anthropic/claude-sonnet-4.5',
  messages,
});

messages.push(...response.messages);
```

---

## Embeddings & Reranking

### Embeddings

```typescript
import { embed, embedMany } from 'ai';
import { openai } from '@ai-sdk/openai';

// Single embedding
const { embedding } = await embed({
  model: openai.embedding('text-embedding-3-small'),
  value: 'Hello world',
});

// Multiple embeddings
const { embeddings } = await embedMany({
  model: openai.embedding('text-embedding-3-small'),
  values: ['Hello', 'World'],
});
```

### Reranking (New in v6)

Reorder search results by relevance:

```typescript
import { rerank } from 'ai';
import { cohere } from '@ai-sdk/cohere';

const { ranking, rerankedDocuments } = await rerank({
  model: cohere.reranking('rerank-v3.5'),
  documents: ['sunny day', 'rainy afternoon', 'snowy night'],
  query: 'weather involving rain',
  topN: 2,
});

// Structured documents
const { rerankedDocuments } = await rerank({
  model: cohere.reranking('rerank-v3.5'),
  documents: [
    { from: 'John', subject: 'Meeting', text: 'Let us meet...' },
    { from: 'Jane', subject: 'Pricing', text: 'Oracle: $5000/mo' },
  ],
  query: 'Oracle pricing',
  topN: 1,
});
```

---

## Image Generation

### generateImage

```typescript
import { generateImage } from 'ai';
import { openai } from '@ai-sdk/openai';

const { images } = await generateImage({
  model: openai.image('dall-e-3'),
  prompt: 'A futuristic city at sunset',
  n: 1,
  size: '1024x1024',
});
```

### Image Editing (New in v6)

```typescript
import { generateImage } from 'ai';
import { blackForestLabs } from '@ai-sdk/black-forest-labs';

const { images } = await generateImage({
  model: blackForestLabs.image('flux-2-pro'),
  prompt: {
    text: 'Add a rainbow to this image',
    images: ['https://example.com/original.png'],
  },
});
```

---

## Language Model Middleware

Wrap models with custom behavior:

```typescript
import { wrapLanguageModel, gateway } from 'ai';

const wrappedModel = wrapLanguageModel({
  model: gateway('anthropic/claude-sonnet-4.5'),
  middleware: myCustomMiddleware(),
});

const result = await generateText({
  model: wrappedModel,
  prompt: 'Hello',
});
```

### DevTools Middleware

```typescript
import { devToolsMiddleware } from '@ai-sdk/devtools';

const model = wrapLanguageModel({
  model: gateway('anthropic/claude-sonnet-4.5'),
  middleware: devToolsMiddleware(),
});

// Run: npx @ai-sdk/devtools
// Open: http://localhost:4983
```

### Add Tool Input Examples Middleware

For providers that don't natively support input examples:

```typescript
import { addToolInputExamplesMiddleware } from 'ai';

const model = wrapLanguageModel({
  model,
  middleware: addToolInputExamplesMiddleware(),
});
```

---

## Provider-Specific Tools

### Anthropic

```typescript
import { anthropic } from '@ai-sdk/anthropic';

// Code execution
const codeExecution = anthropic.tools.codeExecution_20250825();

// Memory
const memory = anthropic.tools.memory_20250818({
  execute: async (action) => { /* ... */ },
});

// Tool search
const toolSearch = anthropic.tools.toolSearchBm25_20251119();
```

### OpenAI

```typescript
import { openai } from '@ai-sdk/openai';

const shell = openai.tools.shell({ execute: async ({ action }) => { /* ... */ } });
const applyPatch = openai.tools.applyPatch({ execute: async ({ operation }) => { /* ... */ } });
const mcp = openai.tools.mcp({ serverUrl: 'https://mcp.example.com' });
```

### Google

```typescript
import { google } from '@ai-sdk/google';

const googleMaps = google.tools.googleMaps();
const fileSearch = google.tools.fileSearch({ fileSearchStoreNames: ['stores/my-store'] });
```

### xAI

```typescript
import { xai } from '@ai-sdk/xai';

const webSearch = xai.tools.webSearch({ allowedDomains: ['wikipedia.org'] });
const xSearch = xai.tools.xSearch({ allowedXHandles: ['elonmusk'] });
const codeExecution = xai.tools.codeExecution();
```