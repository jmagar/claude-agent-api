/**
 * Unit tests for streaming-utils.ts
 *
 * Tests the utility functions used for SSE message handling:
 * - mergeContentBlocks
 * - updateMessagesWithAccumulator
 * - createUserMessage
 * - createAssistantAccumulator
 */

import {
  mergeContentBlocks,
  updateMessagesWithAccumulator,
  createUserMessage,
  createAssistantAccumulator,
} from "@/lib/streaming-utils";
import type { Message, ContentBlock, TextBlock, ThinkingBlock, ToolUseBlock } from "@/types";

describe("streaming-utils", () => {
  describe("mergeContentBlocks", () => {
    it("should append text to existing text block", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [{ type: "text", text: "Hello" }],
        created_at: new Date(),
      };

      const newBlocks: ContentBlock[] = [{ type: "text", text: " World" }];

      const result = mergeContentBlocks(accumulator, newBlocks);

      expect(result.content).toHaveLength(1);
      expect((result.content[0] as TextBlock).text).toBe("Hello World");
    });

    it("should create new text block if no existing text block", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [],
        created_at: new Date(),
      };

      const newBlocks: ContentBlock[] = [{ type: "text", text: "Hello" }];

      const result = mergeContentBlocks(accumulator, newBlocks);

      expect(result.content).toHaveLength(1);
      expect((result.content[0] as TextBlock).text).toBe("Hello");
    });

    it("should add thinking blocks separately", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [{ type: "text", text: "Hello" }],
        created_at: new Date(),
      };

      const newBlocks: ContentBlock[] = [
        { type: "thinking", thinking: "Let me think..." } as ThinkingBlock,
      ];

      const result = mergeContentBlocks(accumulator, newBlocks);

      expect(result.content).toHaveLength(2);
      expect(result.content[0].type).toBe("text");
      expect(result.content[1].type).toBe("thinking");
      expect((result.content[1] as ThinkingBlock).thinking).toBe("Let me think...");
    });

    it("should add tool_use blocks separately", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [{ type: "text", text: "Using a tool" }],
        created_at: new Date(),
      };

      const toolUseBlock: ToolUseBlock = {
        type: "tool_use",
        id: "tool-1",
        name: "read_file",
        input: { path: "/test.txt" },
      };

      const result = mergeContentBlocks(accumulator, [toolUseBlock]);

      expect(result.content).toHaveLength(2);
      expect(result.content[0].type).toBe("text");
      expect(result.content[1].type).toBe("tool_use");
      expect((result.content[1] as ToolUseBlock).name).toBe("read_file");
    });

    it("should handle multiple blocks in sequence", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [],
        created_at: new Date(),
      };

      const blocks1: ContentBlock[] = [{ type: "text", text: "Part 1" }];
      const blocks2: ContentBlock[] = [{ type: "text", text: " Part 2" }];
      const blocks3: ContentBlock[] = [
        { type: "thinking", thinking: "Thinking..." } as ThinkingBlock,
      ];
      const blocks4: ContentBlock[] = [{ type: "text", text: "Part 3" }];

      let result = mergeContentBlocks(accumulator, blocks1);
      result = mergeContentBlocks(result, blocks2);
      result = mergeContentBlocks(result, blocks3);
      result = mergeContentBlocks(result, blocks4);

      expect(result.content).toHaveLength(3);
      expect((result.content[0] as TextBlock).text).toBe("Part 1 Part 2");
      expect(result.content[1].type).toBe("thinking");
      expect((result.content[2] as TextBlock).text).toBe("Part 3");
    });

    it("should not mutate the original accumulator", () => {
      const accumulator: Message = {
        id: "test-1",
        role: "assistant",
        content: [{ type: "text", text: "Original" }],
        created_at: new Date(),
      };

      const originalContent = [...accumulator.content];

      mergeContentBlocks(accumulator, [{ type: "text", text: " Added" }]);

      expect(accumulator.content).toEqual(originalContent);
    });
  });

  describe("updateMessagesWithAccumulator", () => {
    it("should replace existing message with same id", () => {
      const messages: Message[] = [
        {
          id: "msg-1",
          role: "user",
          content: [{ type: "text", text: "Hello" }],
          created_at: new Date(),
        },
        {
          id: "msg-2",
          role: "assistant",
          content: [{ type: "text", text: "Old content" }],
          created_at: new Date(),
        },
      ];

      const accumulator: Message = {
        id: "msg-2",
        role: "assistant",
        content: [{ type: "text", text: "New content" }],
        created_at: new Date(),
      };

      const result = updateMessagesWithAccumulator(messages, accumulator);

      expect(result).toHaveLength(2);
      expect((result[1].content[0] as TextBlock).text).toBe("New content");
    });

    it("should append message if id not found", () => {
      const messages: Message[] = [
        {
          id: "msg-1",
          role: "user",
          content: [{ type: "text", text: "Hello" }],
          created_at: new Date(),
        },
      ];

      const accumulator: Message = {
        id: "msg-2",
        role: "assistant",
        content: [{ type: "text", text: "Response" }],
        created_at: new Date(),
      };

      const result = updateMessagesWithAccumulator(messages, accumulator);

      expect(result).toHaveLength(2);
      expect(result[1].id).toBe("msg-2");
    });

    it("should not mutate original messages array", () => {
      const messages: Message[] = [
        {
          id: "msg-1",
          role: "user",
          content: [{ type: "text", text: "Hello" }],
          created_at: new Date(),
        },
      ];

      const originalLength = messages.length;

      updateMessagesWithAccumulator(messages, {
        id: "msg-2",
        role: "assistant",
        content: [],
        created_at: new Date(),
      });

      expect(messages).toHaveLength(originalLength);
    });

    it("should handle empty messages array", () => {
      const messages: Message[] = [];

      const accumulator: Message = {
        id: "msg-1",
        role: "assistant",
        content: [{ type: "text", text: "First message" }],
        created_at: new Date(),
      };

      const result = updateMessagesWithAccumulator(messages, accumulator);

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("msg-1");
    });
  });

  describe("createUserMessage", () => {
    it("should create a user message with correct structure", () => {
      const text = "Hello, Claude!";

      const result = createUserMessage(text);

      expect(result.role).toBe("user");
      expect(result.content).toHaveLength(1);
      expect(result.content[0].type).toBe("text");
      expect((result.content[0] as TextBlock).text).toBe(text);
    });

    it("should generate id with user- prefix and timestamp", () => {
      const msg1 = createUserMessage("First");

      expect(msg1.id).toMatch(/^user-\d+$/);
    });

    it("should have id starting with user-", () => {
      const result = createUserMessage("Test");

      expect(result.id).toMatch(/^user-\d+$/);
    });

    it("should set created_at to current time", () => {
      const before = new Date();
      const result = createUserMessage("Test");
      const after = new Date();

      expect(result.created_at.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(result.created_at.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it("should handle empty string", () => {
      const result = createUserMessage("");

      expect(result.content).toHaveLength(1);
      expect((result.content[0] as TextBlock).text).toBe("");
    });

    it("should handle multiline text", () => {
      const multilineText = "Line 1\nLine 2\nLine 3";

      const result = createUserMessage(multilineText);

      expect((result.content[0] as TextBlock).text).toBe(multilineText);
    });
  });

  describe("createAssistantAccumulator", () => {
    it("should create an empty assistant message", () => {
      const result = createAssistantAccumulator();

      expect(result.role).toBe("assistant");
      expect(result.content).toEqual([]);
    });

    it("should generate id with assistant- prefix and timestamp", () => {
      const acc1 = createAssistantAccumulator();

      expect(acc1.id).toMatch(/^assistant-\d+$/);
    });

    it("should have id starting with assistant-", () => {
      const result = createAssistantAccumulator();

      expect(result.id).toMatch(/^assistant-\d+$/);
    });

    it("should set created_at to current time", () => {
      const before = new Date();
      const result = createAssistantAccumulator();
      const after = new Date();

      expect(result.created_at.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(result.created_at.getTime()).toBeLessThanOrEqual(after.getTime());
    });
  });
});
