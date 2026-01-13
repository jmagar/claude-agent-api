# AI SDK Agents Reference

## Table of Contents

1. [ToolLoopAgent](#toolloopagent)
2. [Agent Configuration](#agent-configuration)
3. [Call Options](#call-options)
4. [UI Integration](#ui-integration)
5. [MCP Integration](#mcp-integration)
6. [Workflow Patterns](#workflow-patterns)
7. [Custom Agent Implementations](#custom-agent-implementations)

---

## ToolLoopAgent

Production-ready agent abstraction that handles the complete tool execution loop automatically.

### Basic Usage

```typescript
import { ToolLoopAgent } from 'ai';
import { weatherTool } from './tools/weather';

export const weatherAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a helpful weather assistant.',
  tools: {
    weather: weatherTool,
  },
});

const result = await weatherAgent.generate({
  prompt: 'What is the weather in San Francisco?',
});

console.log(result.text);
```

### Streaming

```typescript
const result = await weatherAgent.stream({
  prompt: 'What is the weather in San Francisco?',
});

for await (const text of result.textStream) {
  process.stdout.write(text);
}
```

### How It Works

1. Sends prompt to the LLM
2. If model generates tool calls → executes them
3. Adds tool results back to conversation
4. Repeats until complete or max steps reached (default: 20 steps)

---

## Agent Configuration

### Full Configuration Options

```typescript
import { ToolLoopAgent, stepCountIs, Output } from 'ai';
import { z } from 'zod';

const agent = new ToolLoopAgent({
  // Required
  model: 'anthropic/claude-sonnet-4.5',
  
  // Optional: System instructions
  instructions: 'You are a helpful assistant.',
  
  // Optional: Available tools
  tools: {
    weather: weatherTool,
    search: searchTool,
  },
  
  // Optional: Stop condition (default: stepCountIs(20))
  stopWhen: stepCountIs(10),
  
  // Optional: Structured output
  output: Output.object({
    schema: z.object({
      summary: z.string(),
      data: z.any(),
    }),
  }),
  
  // Optional: Call options schema for type-safe runtime params
  callOptionsSchema: z.object({
    userId: z.string(),
    accountType: z.enum(['free', 'pro', 'enterprise']),
  }),
  
  // Optional: Prepare call for dynamic configuration
  prepareCall: ({ options, ...settings }) => ({
    ...settings,
    instructions: `User: ${options.userId}, Account: ${options.accountType}`,
  }),
});
```

### Stop Conditions

```typescript
import { stepCountIs } from 'ai';

// Stop after N steps
stopWhen: stepCountIs(5)

// Custom condition (future API)
// stopWhen: (step) => step.finishReason === 'stop'
```

---

## Call Options

Pass type-safe arguments when calling agents:

```typescript
import { ToolLoopAgent } from 'ai';
import { z } from 'zod';

const supportAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  
  callOptionsSchema: z.object({
    userId: z.string(),
    accountType: z.enum(['free', 'pro', 'enterprise']),
    documents: z.array(z.string()).optional(),
  }),
  
  prepareCall: ({ options, ...settings }) => ({
    ...settings,
    instructions: `
      You are a customer support agent.
      User Account: ${options.accountType}
      User ID: ${options.userId}
      ${options.documents ? `Context documents:\n${options.documents.join('\n')}` : ''}
    `,
  }),
});

// Call with typed options
const result = await supportAgent.generate({
  prompt: 'How do I upgrade my account?',
  options: {
    userId: 'user_123',
    accountType: 'free',
    documents: ['pricing.md', 'faq.md'],
  },
});
```

### Use Cases for Call Options

- **RAG**: Inject retrieved documents per request
- **Model Selection**: Choose model based on request complexity
- **User Context**: Pass user preferences, permissions, or settings
- **Tool Configuration**: Customize tool behavior per request

---

## UI Integration

### Exporting Types

```typescript
// agents/weather-agent.ts
import { ToolLoopAgent, InferAgentUIMessage } from 'ai';
import { weatherTool } from '@/tools/weather-tool';

export const weatherAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a helpful weather assistant.',
  tools: { weather: weatherTool },
});

export type WeatherAgentUIMessage = InferAgentUIMessage<typeof weatherAgent>;
```

### API Route

```typescript
// app/api/chat/route.ts
import { createAgentUIStreamResponse } from 'ai';
import { weatherAgent } from '@/agents/weather-agent';

export async function POST(request: Request) {
  const { messages } = await request.json();
  
  return createAgentUIStreamResponse({
    agent: weatherAgent,
    uiMessages: messages,
  });
}
```

### Client Component

```typescript
// app/page.tsx
'use client';

import { useChat } from '@ai-sdk/react';
import type { WeatherAgentUIMessage } from '@/agents/weather-agent';
import { WeatherToolView } from '@/components/weather-tool-view';

export default function Chat() {
  const { messages, sendMessage } = useChat<WeatherAgentUIMessage>();
  
  return (
    <div>
      {messages.map(message =>
        message.parts.map((part, index) => {
          switch (part.type) {
            case 'text':
              return <span key={index}>{part.text}</span>;
            case 'tool-weather':
              return <WeatherToolView key={index} invocation={part} />;
            default:
              return null;
          }
        })
      )}
    </div>
  );
}
```

### Typed Tool Components

```typescript
// components/weather-tool-view.tsx
import { UIToolInvocation } from 'ai';
import { weatherTool } from '@/tools/weather-tool';

export function WeatherToolView({
  invocation,
}: {
  invocation: UIToolInvocation<typeof weatherTool>;
}) {
  if (invocation.state === 'call') {
    return <div>Loading weather for {invocation.input.location}...</div>;
  }
  
  if (invocation.state === 'result') {
    return (
      <div>
        Weather in {invocation.input.location}: {invocation.output.temperature}°F
      </div>
    );
  }
  
  return null;
}
```

---

## MCP Integration

### HTTP Transport

```typescript
import { createMCPClient } from '@ai-sdk/mcp';

const mcpClient = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://your-server.com/mcp',
    headers: { Authorization: 'Bearer my-api-key' },
  },
});

const tools = await mcpClient.tools();

const agent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'You are a helpful assistant.',
  tools,
});
```

### SSE Transport

```typescript
const mcpClient = await createMCPClient({
  transport: {
    type: 'sse',
    url: 'https://your-server.com/sse',
  },
});
```

### OAuth Authentication

```typescript
import { createMCPClient, auth, OAuthClientProvider } from '@ai-sdk/mcp';

const authProvider: OAuthClientProvider = {
  redirectUrl: 'http://localhost:3000/callback',
  clientMetadata: {
    client_name: 'My App',
    redirect_uris: ['http://localhost:3000/callback'],
    grant_types: ['authorization_code', 'refresh_token'],
  },
  tokens: async () => { /* return stored tokens */ },
  saveTokens: async (tokens) => { /* save tokens */ },
};

await auth(authProvider, { serverUrl: new URL('https://mcp.example.com') });

const client = await createMCPClient({
  transport: {
    type: 'http',
    url: 'https://mcp.example.com',
    authProvider,
  },
});
```

### MCP Resources and Prompts

```typescript
// List and read resources
const resources = await mcpClient.listResources();
const data = await mcpClient.readResource({
  uri: 'file:///example/document.txt',
});

// List and get prompts
const prompts = await mcpClient.experimental_listPrompts();
const prompt = await mcpClient.experimental_getPrompt({
  name: 'code_review',
  arguments: { code: 'function add(a, b) { return a + b; }' },
});
```

### Elicitation Support

Handle server-initiated requests for user input:

```typescript
const mcpClient = await createMCPClient({
  transport: { type: 'sse', url: 'https://your-server.com/sse' },
  capabilities: { elicitation: {} },
});

mcpClient.onElicitationRequest(ElicitationRequestSchema, async request => {
  const userInput = await getUserInput(
    request.params.message,
    request.params.requestedSchema,
  );

  return {
    action: 'accept',
    content: userInput,
  };
});
```

---

## Workflow Patterns

### Sequential Processing

```typescript
const researchAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'Research the topic thoroughly.',
  tools: { search: searchTool },
});

const summaryAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'Summarize the research findings.',
});

// Chain agents
const research = await researchAgent.generate({
  prompt: 'Research quantum computing',
});

const summary = await summaryAgent.generate({
  prompt: `Summarize: ${research.text}`,
});
```

### Parallel Processing

```typescript
const [weather, news, stocks] = await Promise.all([
  weatherAgent.generate({ prompt: 'Weather in NYC' }),
  newsAgent.generate({ prompt: 'Latest tech news' }),
  stocksAgent.generate({ prompt: 'AAPL stock price' }),
]);
```

### Routing

```typescript
const routerAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: 'Determine which agent should handle this request.',
  output: Output.choice({
    values: ['weather', 'search', 'calculator'],
  }),
});

const { output } = await routerAgent.generate({
  prompt: userQuery,
});

switch (output) {
  case 'weather':
    return weatherAgent.generate({ prompt: userQuery });
  case 'search':
    return searchAgent.generate({ prompt: userQuery });
  case 'calculator':
    return calculatorAgent.generate({ prompt: userQuery });
}
```

### Orchestrator Pattern

```typescript
const orchestratorAgent = new ToolLoopAgent({
  model: 'anthropic/claude-sonnet-4.5',
  instructions: `
    You are an orchestrator. Break down complex tasks and delegate to specialists.
    Available specialists: weather, search, calculator.
  `,
  tools: {
    delegateToWeather: tool({
      description: 'Delegate weather queries',
      inputSchema: z.object({ query: z.string() }),
      execute: async ({ query }) => weatherAgent.generate({ prompt: query }),
    }),
    delegateToSearch: tool({
      description: 'Delegate search queries',
      inputSchema: z.object({ query: z.string() }),
      execute: async ({ query }) => searchAgent.generate({ prompt: query }),
    }),
  },
});
```

---

## Custom Agent Implementations

The `Agent` interface allows building custom agent abstractions:

```typescript
import { Agent } from 'ai';

class MyCustomAgent implements Agent {
  async generate(options: { prompt: string }) {
    // Custom generation logic
  }

  async stream(options: { prompt: string }) {
    // Custom streaming logic
  }
}
```

### DurableAgent (Workflow DevKit)

For production-ready durable agents:

```typescript
import { getWritable } from 'workflow';
import { DurableAgent } from '@workflow/ai/agent';

export async function flightBookingWorkflow() {
  'use workflow';

  const flightAgent = new DurableAgent({
    model: 'anthropic/claude-sonnet-4.5',
    system: 'You are a flight booking assistant.',
    tools: {
      searchFlights,
      bookFlight,
      getFlightStatus,
    },
  });

  const result = await flightAgent.generate({
    prompt: 'Find me a flight from NYC to London next Friday.',
    writable: getWritable(),
  });
}
```

Features:
- Durable, resumable workflows
- Each tool execution is a retryable, observable step
- Automatic state persistence
- Error recovery and retry logic