import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages, UIMessage } from "ai";
import { createClaudeAgent, ClaudeAgentChatSettings } from "@/lib/claude-provider";

export const maxDuration = 300; // Increase timeout for agent operations

export async function POST(req: Request) {
  const {
    messages,
    model,
    sessionId,
    permissionMode,
  }: {
    messages: UIMessage[];
    model: string;
    sessionId?: string;
    permissionMode?: "default" | "acceptEdits" | "plan" | "bypassPermissions";
  } = await req.json();

  const useDirectProvider = process.env.NEXT_PUBLIC_USE_DIRECT_PROVIDER === 'true';

  let languageModel;
  
  if (useDirectProvider) {
    languageModel = openai(model || "gpt-4o");
  } else {
    // Initialize custom provider for FastAPI backend
    const claude = createClaudeAgent({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:54000/api/v1',
      apiKey: process.env.NEXT_PUBLIC_API_KEY, 
    });

    const settings: ClaudeAgentChatSettings = {
        sessionId,
        permissionMode
    };

    languageModel = claude(model || "sonnet", settings);
  }

  const result = streamText({
    model: languageModel,
    messages: await convertToModelMessages(messages),
    // System prompt is often handled by the backend agent presets, but we can pass it if needed
    // system: "You are a helpful assistant...", 
  });

  return result.toUIMessageStreamResponse();
}
