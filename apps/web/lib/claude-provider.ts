import {
  LanguageModelV3,
  LanguageModelV3CallOptions,
  LanguageModelV3Content,
  LanguageModelV3StreamPart,
  LanguageModelV3GenerateResult,
  LanguageModelV3FinishReason,
} from '@ai-sdk/provider';
import {
  withoutTrailingSlash,
} from '@ai-sdk/provider-utils';
import { ProviderV3 } from '@ai-sdk/provider';

type ImageContent = {
  type: 'base64';
  media_type: string;
  data: string;
} | {
  type: 'url';
  data: string;
};

type QueryRequest = {
  prompt: string;
  images?: ImageContent[];
  session_id?: string;
  fork_session?: boolean;
  continue_conversation?: boolean;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  permission_mode?: 'default' | 'acceptEdits' | 'plan' | 'bypassPermissions';
  model?: string;
  enable_file_checkpointing?: boolean;
  include_partial_messages?: boolean;
};

export interface ClaudeAgentProviderSettings {
  baseURL?: string;
  apiKey?: string;
  headers?: Record<string, string>;
}

export interface ClaudeAgentChatSettings {
  sessionId?: string;
  permissionMode?: 'default' | 'acceptEdits' | 'plan' | 'bypassPermissions';
}

export class ClaudeAgentLanguageModel implements LanguageModelV3 {
  readonly specificationVersion = 'v3';
  readonly provider = 'claude-agent';
  readonly modelId: string;
  private config: ClaudeAgentProviderSettings;
  private settings: ClaudeAgentChatSettings;

  constructor(
    modelId: string,
    settings: ClaudeAgentChatSettings,
    config: ClaudeAgentProviderSettings,
  ) {
    this.modelId = modelId;
    this.settings = settings;
    this.config = config;
  }

  get supportedUrls() {
    return {
      'image/*': [/.*/], 
    };
  }

  private getBaseUrl(): string {
    return withoutTrailingSlash(this.config.baseURL ?? 'http://localhost:54000/api/v1') || 'http://localhost:54000/api/v1';
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...this.config.headers,
    };
    if (this.config.apiKey) {
      headers['X-API-Key'] = this.config.apiKey;
    }
    return headers;
  }

  private prepareRequest(options: LanguageModelV3CallOptions): QueryRequest {
    const lastUserMessage = [...options.prompt].reverse().find(m => m.role === 'user');
    
    if (!lastUserMessage) {
      throw new Error('No user message found in prompt');
    }

    let promptText = '';
    const images: ImageContent[] = [];

    for (const part of lastUserMessage.content) {
      if (part.type === 'text') {
        promptText += part.text + '\n';
      } else if (part.type === 'file') {
        if (part.data instanceof Uint8Array) {
           promptText += `[Image: ${part.mediaType}]\n`;
           const base64 = typeof Buffer !== 'undefined' 
              ? Buffer.from(part.data).toString('base64') 
              : btoa(String.fromCharCode(...new Uint8Array(part.data)));
           
           images.push({
             type: 'base64',
             media_type: part.mediaType,
             data: base64,
           });
        } else if (typeof part.data === 'string') {
          images.push({
            type: 'base64',
            media_type: part.mediaType,
            data: part.data,
          });
        } else if (part.data instanceof URL) {
           images.push({
             type: 'url',
             data: part.data.toString(),
           });
        }
      }
    }

    promptText = promptText.trim();

    if (!promptText) {
      throw new Error('Prompt is empty after processing message parts');
    }

    return {
      prompt: promptText,
      images: images.length > 0 ? images : undefined,
      session_id: this.settings.sessionId,
      permission_mode: this.settings.permissionMode,
      model: this.modelId,
      include_partial_messages: true,
    };
  }

  async doGenerate(options: LanguageModelV3CallOptions): Promise<LanguageModelV3GenerateResult> {
    const { stream } = await this.doStream(options);
    const content: LanguageModelV3Content[] = [];
    let usage = {
        inputTokens: { total: 0, noCache: 0, cacheRead: 0, cacheWrite: 0 },
        outputTokens: { total: 0, text: 0, reasoning: 0 }
    } as any;
    let finishReason: LanguageModelV3FinishReason = 'other' as unknown as LanguageModelV3FinishReason;

    const reader = stream.getReader();
    let textContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      if (value.type === 'text-delta') {
        textContent += value.delta;
      } else if (value.type === 'finish') {
        finishReason = value.finishReason;
        if (value.usage) {
            usage = value.usage;
        }
      }
    }

    if (textContent) {
      content.push({ type: 'text', text: textContent });
    }

    return {
      content,
      finishReason,
      usage,
      warnings: [],
    };
  }

  async doStream(options: LanguageModelV3CallOptions): Promise<{
    stream: ReadableStream<LanguageModelV3StreamPart>;
    warnings?: any[];
  }> {
    const requestBody = this.prepareRequest(options);

    // Note: The API requires authentication
    const response = await fetch(`${this.getBaseUrl()}/query`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
        const errorBody = await response.text();
        console.error('API Error Response:', errorBody);
        throw new Error(`API call failed: ${response.statusText} - ${errorBody}`);
    }

    if (!response.body) {
        throw new Error('No response body');
    }

    const sseParser = this.createSseParser();

    const stream = response.body
      .pipeThrough(new TextDecoderStream())
      .pipeThrough(sseParser);

    return { stream, warnings: [] };
  }

  private createSseParser(): TransformStream<string, LanguageModelV3StreamPart> {
    let buffer = '';
    let eventType: string | null = null;
    
    const activeBlocks: Record<number, { type: string; id?: string; name?: string }> = {};

    return new TransformStream({
      transform(chunk, controller) {
        buffer += chunk;
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; 

        for (const line of lines) {
            if (!line.trim()) {
                eventType = null;
                continue;
            }

            if (line.startsWith('event: ')) {
                eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
                const dataStr = line.slice(6);
                try {
                    const data = JSON.parse(dataStr);

                     if (eventType === 'message') {
                        // Skip message events in favor of partial streaming events
                        // The 'message' event contains the complete response, but we want streaming
                        // Only process tool calls from message events
                        if (data.type === 'assistant') {
                           for (const block of data.content) {
                               if (block.type === 'tool_use') {
                                   controller.enqueue({
                                       type: 'tool-call',
                                       toolCallId: block.id,
                                       toolName: block.name,
                                       args: JSON.stringify(block.input)
                                   } as any);
                               }
                           }
                        }
                     } else if (eventType === 'partial') {
                        if (data.type === 'content_block_start') {
                            if (data.content_block) {
                                activeBlocks[data.index] = {
                                    type: data.content_block.type,
                                    id: data.content_block.id,
                                    name: data.content_block.name
                                };

                                if (data.content_block.type === 'text') {
                                    controller.enqueue({
                                        type: 'text-start',
                                        id: data.content_block.id || 'unknown'
                                    });
                                } else if (data.content_block.type === 'tool_use') {
                                    controller.enqueue({
                                        type: 'tool-input-start',
                                        toolName: data.content_block.name || 'unknown',
                                        id: data.content_block.id || 'unknown'
                                    });
                                }
                            }
                        } else if (data.type === 'content_block_delta') {
                            const block = activeBlocks[data.index];
                            if (data.delta.type === 'text_delta') {
                                controller.enqueue({ 
                                    type: 'text-delta', 
                                    delta: data.delta.text,
                                    id: block?.id || 'unknown'
                                });
                            } else if (data.delta.type === 'input_json_delta' && block?.type === 'tool_use') {
                                controller.enqueue({ 
                                    type: 'tool-input-delta', 
                                    id: block.id!,
                                    delta: data.delta.partial_json,
                                });
                            } else if (data.delta.type === 'thinking_delta') {
                                // Maps to reasoning
                                controller.enqueue({
                                    type: 'reasoning-delta',
                                    delta: data.delta.thinking,
                                    id: block?.id || 'unknown'
                                }); 
                            }
                        } else if (data.type === 'content_block_stop') {
                             const block = activeBlocks[data.index];
                             if (block?.type === 'text') {
                                 controller.enqueue({
                                     type: 'text-end',
                                     id: block.id || 'unknown'
                                 });
                             } else if (block?.type === 'tool_use'){
                                 controller.enqueue({
                                     type: 'tool-input-end',
                                     id: block.id || 'unknown'
                                 });
                             }
                             delete activeBlocks[data.index];
                        }
                     } else if (eventType === 'result') {
                         if (data.usage) {
                             const inputTokens = data.usage.input_tokens || 0;
                             const outputTokens = data.usage.output_tokens || 0;

                             controller.enqueue({
                                 type: 'finish',
                                 finishReason: 'stop' as unknown as LanguageModelV3FinishReason,
                                 usage: {
                                    inputTokens: {
                                        total: inputTokens,
                                        noCache: inputTokens, // assume no cache if not provided
                                        cacheRead: 0,
                                        cacheWrite: 0
                                    },
                                    outputTokens: {
                                        total: outputTokens,
                                        text: outputTokens,
                                        reasoning: 0
                                    }
                                 }
                             });
                         }
                     } else if (eventType === 'done') {
                         // Stream is complete - terminate the stream
                         controller.terminate();
                     } else if (eventType === 'error') {
                         // Error occurred - emit error and close stream
                         controller.error(new Error(data.message || 'Unknown error'));
                     }
                } catch (e) {
                    console.error('Failed to parse SSE JSON', e);
                }
            }
        }
      }
    });
  }
}

export function createClaudeAgent(options: ClaudeAgentProviderSettings = {}) {
  const createModel = (modelId: string, settings: ClaudeAgentChatSettings = {}) => {
    return new ClaudeAgentLanguageModel(modelId, settings, options);
  };

  const provider = function (modelId: string, settings: ClaudeAgentChatSettings = {}) {
     return createModel(modelId, settings);
  } as any;
  
  provider.languageModel = createModel;

  return provider as ProviderV3 & {
      (modelId: string, settings?: ClaudeAgentChatSettings): ClaudeAgentLanguageModel;
      languageModel(modelId: string, settings?: ClaudeAgentChatSettings): ClaudeAgentLanguageModel;
  }; 
}
