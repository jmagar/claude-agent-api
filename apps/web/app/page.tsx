"use client";

import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageActions,
  MessageAction,
  MessageAttachment,
  MessageAttachments,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputButton,
  PromptInputHeader,
  type PromptInputMessage,
  PromptInputSelect,
  PromptInputSelectContent,
  PromptInputSelectItem,
  PromptInputSelectTrigger,
  PromptInputSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import {
  Tool,
  ToolHeader,
  ToolContent,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import {
  ChainOfThought,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
  ChainOfThoughtContent,
} from "@/components/ai-elements/chain-of-thought";
import {
  Artifact,
  ArtifactHeader,
  ArtifactTitle,
  ArtifactContent,
  ArtifactActions,
  ArtifactAction,
} from "@/components/ai-elements/artifact";
import { CodeBlock } from "@/components/ai-elements/code-block";
import {
  Plan,
  PlanHeader,
  PlanTitle,
  PlanDescription,
  PlanContent,
} from "@/components/ai-elements/plan";
import {
  Task,
  TaskTrigger,
  TaskContent,
  TaskItem,
  TaskItemFile,
} from "@/components/ai-elements/task";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { Suggestions, Suggestion } from "@/components/ai-elements/suggestion";
import { Loader } from "@/components/ai-elements/loader";
import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import {
  CopyIcon,
  GlobeIcon,
  RefreshCcwIcon,
  MessageSquareIcon,
  CodeIcon,
  FileIcon,
} from "lucide-react";
import type { FileUIPart } from "ai";

// Extended message part types for custom content
type PlanPart = {
  type: "plan";
  title?: string;
  description?: string;
  content?: string;
  text?: string;
};

type TaskPart = {
  type: "task";
  title?: string;
  items?: Array<{ text: string; files?: string[] } | string>;
  content?: string;
  text?: string;
};

type ChainOfThoughtPart = {
  type: "chain-of-thought";
  items?: Array<{ text: string } | string>;
  content?: string;
  text?: string;
};

type ArtifactPart = {
  type: "artifact";
  title?: string;
  language?: string;
  content?: string;
  text?: string;
};

const models = [
  {
    name: "Claude Sonnet 4.5",
    value: "sonnet",
  },
  {
    name: "Claude Opus 4.5",
    value: "opus",
  },
  {
    name: "Claude Haiku 4.5",
    value: "haiku",
  },
];

const suggestions = [
  "What can you help me with?",
  "Explain quantum computing",
  "Write a haiku about coding",
  "Help me debug my code",
];

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [model, setModel] = useState<string>(models[1]?.value ?? "gpt-4o-mini");
  const [webSearch, setWebSearch] = useState(false);
  const { messages, sendMessage, status, regenerate } = useChat();

  const handleSubmit = (message: PromptInputMessage) => {
    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    sendMessage(
      {
        text: message.text ?? "Sent with attachments",
        files: message.files,
      },
      {
        body: {
          model: model,
          webSearch: webSearch,
        },
      }
    );
    setInput("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(
      { text: suggestion },
      {
        body: {
          model: model,
          webSearch: webSearch,
        },
      }
    );
  };

  const isLastAssistantMessage = (messageId: string, partIndex: number) => {
    const lastMessage = messages.at(-1);
    return (
      lastMessage?.id === messageId &&
      lastMessage?.role === "assistant" &&
      partIndex === lastMessage.parts.length - 1
    );
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
  };

  const extractCodeBlocks = (text: string) => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const blocks: Array<{
      language: string;
      code: string;
      start: number;
      end: number;
    }> = [];
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      blocks.push({
        language: match[1] || "typescript",
        code: match[2] || "",
        start: match.index,
        end: match.index + match[0].length,
      });
    }

    return blocks;
  };

  const renderTextWithCodeBlocks = (text: string, messageId: string) => {
    const codeBlocks = extractCodeBlocks(text);

    if (codeBlocks.length === 0) {
      return <MessageResponse>{text}</MessageResponse>;
    }

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    codeBlocks.forEach((block, i) => {
      // Add text before code block
      if (block.start > lastIndex) {
        parts.push(
          <MessageResponse key={`text-${messageId}-${i}`}>
            {text.slice(lastIndex, block.start)}
          </MessageResponse>
        );
      }

      // Add code block
      parts.push(
        <Artifact key={`code-${messageId}-${i}`} className="my-2">
          <ArtifactHeader>
            <div className="flex items-center gap-2">
              <CodeIcon className="size-4" />
              <ArtifactTitle>{block.language}</ArtifactTitle>
            </div>
            <ArtifactActions>
              <ArtifactAction
                onClick={() => handleCopyCode(block.code)}
                tooltip="Copy code"
                size="sm"
                variant="ghost"
              >
                <CopyIcon className="size-3" />
              </ArtifactAction>
            </ArtifactActions>
          </ArtifactHeader>
          <ArtifactContent>
            <CodeBlock
              code={block.code}
              language={block.language as any}
              showLineNumbers={block.code.split("\n").length > 10}
            />
          </ArtifactContent>
        </Artifact>
      );

      lastIndex = block.end;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <MessageResponse key={`text-${messageId}-final`}>
          {text.slice(lastIndex)}
        </MessageResponse>
      );
    }

    return <>{parts}</>;
  };

  return (
    <div className="relative size-full h-screen max-w-4xl mx-auto p-6">
      <div className="flex flex-col h-full">
        <Conversation className="h-full">
          <ConversationContent>
            {messages.length === 0 ? (
              <ConversationEmptyState
                title="Start a conversation"
                description="Ask me anything or choose a suggestion below"
                icon={<MessageSquareIcon className="size-8" />}
              >
                <div className="mt-6">
                  <Suggestions>
                    {suggestions.map((suggestion) => (
                      <Suggestion
                        key={suggestion}
                        suggestion={suggestion}
                        onClick={handleSuggestionClick}
                      />
                    ))}
                  </Suggestions>
                </div>
              </ConversationEmptyState>
            ) : (
              messages.map((message) => (
                <div key={message.id} className="space-y-4">
                  {/* Sources section for assistant messages */}
                  {message.role === "assistant" &&
                    message.parts.filter((part) => part.type === "source-url")
                      .length > 0 && (
                      <Sources>
                        <SourcesTrigger
                          count={
                            message.parts.filter(
                              (part) => part.type === "source-url"
                            ).length
                          }
                        />
                        <SourcesContent>
                          {message.parts
                            .filter((part) => part.type === "source-url")
                            .map((part, i) => (
                              <Source
                                key={`source-${message.id}-${i}`}
                                href={part.url}
                                title={part.title ?? part.url}
                              />
                            ))}
                        </SourcesContent>
                      </Sources>
                    )}

                  {/* File attachments for user messages */}
                  {message.role === "user" && (
                    <MessageAttachments>
                      {message.parts
                        .filter((part): part is FileUIPart => part.type === "file")
                        .map((filePart, i) => (
                          <MessageAttachment
                            key={`file-${message.id}-${i}`}
                            data={filePart}
                          />
                        ))}
                    </MessageAttachments>
                  )}

                  {/* Message parts */}
                  {message.parts.map((part, i) => {
                    const partKey = `${message.id}-${i}`;

                    // Type assertion for extended part types
                    const partType = part.type as string;

                    switch (partType) {
                      case "text": {
                        const textPart = part as any;
                        return (
                          <Message key={partKey} from={message.role}>
                            <MessageContent>
                              {renderTextWithCodeBlocks(textPart.text, partKey)}
                            </MessageContent>
                            {message.role === "assistant" &&
                              isLastAssistantMessage(message.id, i) && (
                                <MessageActions>
                                  <MessageAction
                                    onClick={() => regenerate()}
                                    label="Retry"
                                    tooltip="Regenerate response"
                                  >
                                    <RefreshCcwIcon className="size-3" />
                                  </MessageAction>
                                  <MessageAction
                                    onClick={() =>
                                      navigator.clipboard.writeText(textPart.text)
                                    }
                                    label="Copy"
                                    tooltip="Copy to clipboard"
                                  >
                                    <CopyIcon className="size-3" />
                                  </MessageAction>
                                </MessageActions>
                              )}
                          </Message>
                        );
                      }

                      case "reasoning": {
                        const reasoningPart = part as any;
                        return (
                          <Reasoning
                            key={partKey}
                            className="w-full"
                            isStreaming={
                              status === "streaming" &&
                              message.id === messages.at(-1)?.id &&
                              i === message.parts.length - 1
                            }
                          >
                            <ReasoningTrigger />
                            <ReasoningContent>{reasoningPart.text}</ReasoningContent>
                          </Reasoning>
                        );
                      }

                      case "tool-invocation": {
                        const toolPart = part as any;
                        return (
                          <Tool key={partKey}>
                            <ToolHeader
                              title={toolPart.title}
                              type={toolPart.type}
                              state={toolPart.state}
                            />
                            <ToolContent>
                              <ToolInput input={toolPart.input} />
                              {toolPart.output !== undefined && (
                                <ToolOutput
                                  output={toolPart.output}
                                  errorText={toolPart.errorText}
                                />
                              )}
                            </ToolContent>
                          </Tool>
                        );
                      }

                      case "file":
                        // File parts are handled above in MessageAttachments
                        return null;

                      case "source-url":
                        // Source URLs are handled in the Sources section above
                        return null;

                      case "plan": {
                        const planPart = part as unknown as PlanPart;
                        return (
                          <Plan
                            key={partKey}
                            isStreaming={
                              status === "streaming" &&
                              message.id === messages.at(-1)?.id &&
                              i === message.parts.length - 1
                            }
                          >
                            <PlanHeader>
                              <PlanTitle>
                                {planPart.title || "Implementation Plan"}
                              </PlanTitle>
                              {planPart.description && (
                                <PlanDescription>{planPart.description}</PlanDescription>
                              )}
                            </PlanHeader>
                            <PlanContent>
                              <MessageResponse>
                                {planPart.content || planPart.text || ""}
                              </MessageResponse>
                            </PlanContent>
                          </Plan>
                        );
                      }

                      case "task": {
                        const taskPart = part as unknown as TaskPart;
                        return (
                          <Task key={partKey}>
                            <TaskTrigger title={taskPart.title || "Task"} />
                            <TaskContent>
                              {taskPart.items?.map((item, idx) => (
                                <TaskItem key={`${partKey}-item-${idx}`}>
                                  {typeof item === "string"
                                    ? item
                                    : item.text}
                                  {typeof item === "object" &&
                                    item.files?.map((file, fileIdx) => (
                                      <TaskItemFile key={`${partKey}-file-${fileIdx}`}>
                                        <FileIcon className="size-3" />
                                        {file}
                                      </TaskItemFile>
                                    ))}
                                </TaskItem>
                              )) || (
                                <TaskItem>
                                  <MessageResponse>
                                    {taskPart.content || taskPart.text || ""}
                                  </MessageResponse>
                                </TaskItem>
                              )}
                            </TaskContent>
                          </Task>
                        );
                      }

                      case "chain-of-thought": {
                        const cotPart = part as unknown as ChainOfThoughtPart;
                        return (
                          <ChainOfThought key={partKey}>
                            <ChainOfThoughtHeader />
                            <ChainOfThoughtContent>
                              {cotPart.items?.map((item, idx) => (
                                <ChainOfThoughtStep
                                  key={`${partKey}-item-${idx}`}
                                  label={
                                    typeof item === "string"
                                      ? item
                                      : item.text
                                  }
                                  status="complete"
                                />
                              )) || (
                                <MessageResponse>
                                  {cotPart.content || cotPart.text || ""}
                                </MessageResponse>
                              )}
                            </ChainOfThoughtContent>
                          </ChainOfThought>
                        );
                      }

                      case "artifact": {
                        const artifactPart = part as unknown as ArtifactPart;
                        return (
                          <Artifact key={partKey} className="my-2">
                            <ArtifactHeader>
                              <ArtifactTitle>
                                {artifactPart.title || "Artifact"}
                              </ArtifactTitle>
                              <ArtifactActions>
                                <ArtifactAction
                                  onClick={() =>
                                    handleCopyCode(
                                      artifactPart.content || artifactPart.text || ""
                                    )
                                  }
                                  tooltip="Copy content"
                                  size="sm"
                                  variant="ghost"
                                >
                                  <CopyIcon className="size-3" />
                                </ArtifactAction>
                              </ArtifactActions>
                            </ArtifactHeader>
                            <ArtifactContent>
                              {artifactPart.language ? (
                                <CodeBlock
                                  code={artifactPart.content || artifactPart.text || ""}
                                  language={artifactPart.language as any}
                                  showLineNumbers
                                />
                              ) : (
                                <MessageResponse>
                                  {artifactPart.content || artifactPart.text || ""}
                                </MessageResponse>
                              )}
                            </ArtifactContent>
                          </Artifact>
                        );
                      }

                      default:
                        return null;
                    }
                  })}
                </div>
              ))
            )}
            {status === "submitted" && (
              <div className="flex items-center gap-2">
                <Loader />
                <Shimmer className="text-sm">Thinking...</Shimmer>
              </div>
            )}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <PromptInput
          onSubmit={handleSubmit}
          className="mt-4"
          globalDrop
          multiple
        >
          <PromptInputHeader>
            <PromptInputAttachments>
              {(attachment) => <PromptInputAttachment data={attachment} />}
            </PromptInputAttachments>
          </PromptInputHeader>
          <PromptInputBody>
            <PromptInputTextarea
              onChange={(e) => setInput(e.target.value)}
              value={input}
              placeholder="Type a message..."
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputActionMenu>
                <PromptInputActionMenuTrigger />
                <PromptInputActionMenuContent>
                  <PromptInputActionAddAttachments />
                </PromptInputActionMenuContent>
              </PromptInputActionMenu>
              <PromptInputButton
                variant={webSearch ? "default" : "ghost"}
                onClick={() => setWebSearch(!webSearch)}
              >
                <GlobeIcon size={16} />
                <span>Search</span>
              </PromptInputButton>
              <PromptInputSelect
                onValueChange={(value) => {
                  setModel(value);
                }}
                value={model}
              >
                <PromptInputSelectTrigger>
                  <PromptInputSelectValue />
                </PromptInputSelectTrigger>
                <PromptInputSelectContent>
                  {models.map((m) => (
                    <PromptInputSelectItem key={m.value} value={m.value}>
                      {m.name}
                    </PromptInputSelectItem>
                  ))}
                </PromptInputSelectContent>
              </PromptInputSelect>
            </PromptInputTools>
            <PromptInputSubmit
              disabled={!input && status !== "streaming"}
              status={status}
            />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
}
