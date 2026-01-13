# AI SDK UI Reference

## Table of Contents

1. [useChat Hook](#usechat-hook)
2. [Message Handling](#message-handling)
3. [Status and Error Handling](#status-and-error-handling)
4. [Transport Configuration](#transport-configuration)
5. [File Attachments](#file-attachments)
6. [Tool Invocations in UI](#tool-invocations-in-ui)
7. [useCompletion Hook](#usecompletion-hook)
8. [useObject Hook](#useobject-hook)

---

## useChat Hook

The `useChat` hook creates a conversational interface with real-time streaming.

### Basic Usage

```typescript
'use client';

import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';

export default function Chat() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/chat',
    }),
  });
  const [input, setInput] = useState('');

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.parts.map((part, index) =>
            part.type === 'text' ? <span key={index}>{part.text}</span> : null
          )}
        </div>
      ))}

      <form
        onSubmit={e => {
          e.preventDefault();
          if (input.trim()) {
            sendMessage({ text: input });
            setInput('');
          }
        }}
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={status !== 'ready'}
          placeholder="Say something..."
        />
        <button type="submit" disabled={status !== 'ready'}>
          Submit
        </button>
      </form>
    </>
  );
}
```

### API Route

```typescript
// app/api/chat/route.ts
import { convertToModelMessages, streamText, UIMessage } from 'ai';

export const maxDuration = 30; // Allow streaming up to 30 seconds

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: 'anthropic/claude-sonnet-4.5',
    system: 'You are a helpful assistant.',
    messages: await convertToModelMessages(messages),
  });

  return result.toUIMessageStreamResponse();
}
```

---

## Message Handling

### Message Parts

Messages use a `parts` array for flexible content types:

```typescript
message.parts.map((part, index) => {
  switch (part.type) {
    case 'text':
      return <span key={index}>{part.text}</span>;
    case 'reasoning':
      return <pre key={index}>{part.text}</pre>;
    case 'file':
      if (part.mediaType?.startsWith('image/')) {
        return <img key={index} src={part.url} alt={part.filename} />;
      }
      return null;
    case 'source-url':
      return <a key={index} href={part.url}>{part.title}</a>;
    case 'tool-invocation':
      return <ToolView key={index} invocation={part} />;
    default:
      return null;
  }
});
```

### Modifying Messages

```typescript
const { messages, setMessages } = useChat();

// Delete a message
const handleDelete = (id: string) => {
  setMessages(messages.filter(m => m.id !== id));
};

// Edit messages directly
setMessages([...messages, newMessage]);
```

### Message Metadata

Attach custom metadata to messages:

```typescript
// Server: Send metadata
return result.toUIMessageStreamResponse({
  messageMetadata: ({ part }) => {
    if (part.type === 'start') {
      return { createdAt: Date.now(), model: 'gpt-4' };
    }
    if (part.type === 'finish') {
      return { totalTokens: part.totalUsage.totalTokens };
    }
  },
});

// Client: Access metadata
{messages.map(message => (
  <div key={message.id}>
    {message.metadata?.createdAt && new Date(message.metadata.createdAt).toLocaleTimeString()}
    {message.parts.map((part, i) => /* ... */)}
    {message.metadata?.totalTokens && <span>{message.metadata.totalTokens} tokens</span>}
  </div>
))}
```

---

## Status and Error Handling

### Status States

```typescript
const { status, stop, reload } = useChat();

// Status values:
// 'submitted' - Sent to API, waiting for response
// 'streaming' - Receiving chunks from API
// 'ready' - Complete, ready for new input
// 'error' - Request failed

// Show loading state
{(status === 'submitted' || status === 'streaming') && (
  <div>
    {status === 'submitted' && <Spinner />}
    <button onClick={() => stop()}>Stop</button>
  </div>
)}

// Disable input when not ready
<button type="submit" disabled={status !== 'ready'}>Send</button>
```

### Error Handling

```typescript
const { error, reload } = useChat();

{error && (
  <>
    <div>An error occurred.</div>
    <button onClick={() => reload()}>Retry</button>
  </>
)}
```

### Regeneration

```typescript
const { regenerate, status } = useChat();

<button
  onClick={regenerate}
  disabled={!(status === 'ready' || status === 'error')}
>
  Regenerate
</button>
```

### Throttling Updates

```typescript
const { messages } = useChat({
  experimental_throttle: 50, // Update UI every 50ms max
});
```

---

## Transport Configuration

### Default Transport

```typescript
import { DefaultChatTransport } from 'ai';

const { messages, sendMessage } = useChat({
  transport: new DefaultChatTransport({
    api: '/api/chat',
    headers: {
      Authorization: 'Bearer token',
    },
    body: {
      userId: '123',
    },
    credentials: 'same-origin',
  }),
});
```

### Dynamic Configuration

```typescript
const { messages, sendMessage } = useChat({
  transport: new DefaultChatTransport({
    api: '/api/chat',
    headers: () => ({
      Authorization: `Bearer ${getAuthToken()}`,
    }),
    body: () => ({
      sessionId: getCurrentSessionId(),
    }),
  }),
});
```

### Request-Level Options

```typescript
sendMessage(
  { text: input },
  {
    headers: { 'X-Custom-Header': 'value' },
    body: { temperature: 0.7, max_tokens: 100 },
    metadata: { userId: 'user123' },
  }
);
```

### Custom Request Preparation

```typescript
const { messages, sendMessage } = useChat({
  id: 'my-chat',
  transport: new DefaultChatTransport({
    prepareSendMessagesRequest: ({ id, messages, trigger, messageId }) => {
      if (trigger === 'submit-user-message') {
        return {
          body: {
            trigger: 'submit-user-message',
            id,
            message: messages[messages.length - 1],
          },
        };
      } else if (trigger === 'regenerate-assistant-message') {
        return {
          body: {
            trigger: 'regenerate-assistant-message',
            id,
            messageId,
          },
        };
      }
      throw new Error(`Unsupported trigger: ${trigger}`);
    },
  }),
});
```

### Text Stream Transport

For simple text-only streaming:

```typescript
import { TextStreamChatTransport } from 'ai';

const { messages } = useChat({
  transport: new TextStreamChatTransport({
    api: '/api/chat',
  }),
});
```

---

## File Attachments

### Using FileList

```typescript
const [files, setFiles] = useState<FileList | undefined>(undefined);
const fileInputRef = useRef<HTMLInputElement>(null);

<form
  onSubmit={e => {
    e.preventDefault();
    sendMessage({ text: input, files });
    setFiles(undefined);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }}
>
  <input
    type="file"
    multiple
    ref={fileInputRef}
    onChange={e => setFiles(e.target.files ?? undefined)}
  />
  <input value={input} onChange={e => setInput(e.target.value)} />
</form>
```

### Using File Objects

```typescript
import { FileUIPart } from 'ai';

const files: FileUIPart[] = [
  {
    type: 'file',
    filename: 'image.png',
    mediaType: 'image/png',
    url: 'https://example.com/image.png',
  },
  {
    type: 'file',
    filename: 'document.txt',
    mediaType: 'text/plain',
    url: 'data:text/plain;base64,SGVsbG8gV29ybGQ=',
  },
];

sendMessage({ text: 'Analyze these files', files });
```

### Rendering File Parts

```typescript
message.parts.map((part, index) => {
  if (part.type === 'file' && part.mediaType?.startsWith('image/')) {
    return <img key={index} src={part.url} alt={part.filename} />;
  }
});
```

---

## Tool Invocations in UI

### Rendering Tool Calls

```typescript
message.parts.map((part, index) => {
  if (part.type === 'tool-invocation') {
    switch (part.state) {
      case 'call':
        return <div key={index}>Calling {part.toolName}...</div>;
      case 'result':
        return <div key={index}>Result: {JSON.stringify(part.result)}</div>;
    }
  }
});
```

### Tool Execution Approval

```typescript
import { ChatAddToolApprovalResponseFunction, UIToolInvocation } from 'ai';

function ToolApprovalView({
  invocation,
  addToolApprovalResponse,
}: {
  invocation: UIToolInvocation<typeof myTool>;
  addToolApprovalResponse: ChatAddToolApprovalResponseFunction;
}) {
  if (invocation.state === 'approval-requested') {
    return (
      <div>
        <p>Run: {invocation.input.command}?</p>
        <button
          onClick={() =>
            addToolApprovalResponse({
              id: invocation.approval.id,
              approved: true,
            })
          }
        >
          Approve
        </button>
        <button
          onClick={() =>
            addToolApprovalResponse({
              id: invocation.approval.id,
              approved: false,
            })
          }
        >
          Deny
        </button>
      </div>
    );
  }

  if (invocation.state === 'output-available') {
    return <div>Output: {invocation.output}</div>;
  }

  return null;
}
```

### Type-Safe Tool Components

```typescript
import { InferUITool, InferUITools, UIMessage, UIDataTypes } from 'ai';

// Single tool type
type WeatherUITool = InferUITool<typeof weatherTool>;

// Multiple tools
const tools = { weather: weatherTool, calculator: calculatorTool };
type MyUITools = InferUITools<typeof tools>;

// Custom message type
type MyUIMessage = UIMessage<never, UIDataTypes, MyUITools>;

// Use with hook
const { messages } = useChat<MyUIMessage>();

// Render with type safety
function WeatherToolView({ invocation }: { invocation: UIToolInvocation<typeof weatherTool> }) {
  return <div>Weather: {invocation.output?.temperature}°F</div>;
}
```

---

## Event Callbacks

```typescript
const { messages } = useChat({
  onFinish: ({ message, messages, isAbort, isDisconnect, isError }) => {
    console.log('Finished:', message);
  },
  onError: error => {
    console.error('Error:', error);
  },
  onData: data => {
    console.log('Data part:', data);
    // Throw to abort processing
    // throw new Error('Stop processing');
  },
});
```

---

## useCompletion Hook

For simple text completion (not chat):

```typescript
import { useCompletion } from '@ai-sdk/react';

const { completion, input, setInput, handleSubmit, isLoading } = useCompletion({
  api: '/api/completion',
});

<form onSubmit={handleSubmit}>
  <input value={input} onChange={e => setInput(e.target.value)} />
  <button type="submit" disabled={isLoading}>Complete</button>
</form>
<p>{completion}</p>
```

---

## useObject Hook

Stream structured objects:

```typescript
import { useObject } from '@ai-sdk/react';
import { z } from 'zod';

const recipeSchema = z.object({
  name: z.string(),
  ingredients: z.array(z.object({
    name: z.string(),
    amount: z.string(),
  })),
});

const { object, submit, isLoading } = useObject({
  api: '/api/recipe',
  schema: recipeSchema,
});

<button onClick={() => submit('Generate a pasta recipe')}>Generate</button>
{object && (
  <div>
    <h2>{object.name}</h2>
    {object.ingredients?.map((ing, i) => (
      <p key={i}>{ing.amount} {ing.name}</p>
    ))}
  </div>
)}
```

---

## Server-Side Streaming Options

### Reasoning Tokens

```typescript
// Server
return result.toUIMessageStreamResponse({
  sendReasoning: true,
});

// Client
message.parts.map((part, i) => {
  if (part.type === 'reasoning') {
    return <pre key={i}>{part.text}</pre>;
  }
});
```

### Sources

```typescript
// Server
return result.toUIMessageStreamResponse({
  sendSources: true,
});

// Client
message.parts.filter(p => p.type === 'source-url').map(source => (
  <a key={source.id} href={source.url}>{source.title}</a>
));
```

### Error Messages

```typescript
return result.toUIMessageStreamResponse({
  onError: error => {
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    return 'An error occurred';
  },
});
```

### Usage Information

```typescript
// Server
return result.toUIMessageStreamResponse({
  messageMetadata: ({ part }) => {
    if (part.type === 'finish') {
      return { totalUsage: part.totalUsage };
    }
  },
});

// Client
{message.metadata?.totalUsage?.totalTokens && (
  <span>{message.metadata.totalUsage.totalTokens} tokens</span>
)}
```