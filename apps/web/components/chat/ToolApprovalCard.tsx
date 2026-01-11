/**
 * ToolApprovalCard component
 *
 * Displays an inline approval request for a tool call with:
 * - Tool name and target path
 * - "Always allow this tool" checkbox
 * - Approve and Reject actions
 */

"use client";

import { memo, useState } from "react";
import type { ToolCall } from "@/types";

export interface ToolApprovalCardProps {
  toolCall: ToolCall;
  onApprove: (remember: boolean) => void;
  onReject: () => void;
}

export const ToolApprovalCard = memo(function ToolApprovalCard({
  toolCall,
  onApprove,
  onReject,
}: ToolApprovalCardProps) {
  const [remember, setRemember] = useState(false);
  const toolPath =
    typeof toolCall.input?.path === "string" ? toolCall.input.path : null;

  return (
    <div
      data-testid="tool-approval-card"
      className="rounded-8 border border-yellow-200 bg-yellow-50 p-16"
    >
      <div className="text-12 font-semibold uppercase text-yellow-700">
        Tool Approval Required
      </div>
      <div className="mt-8 text-14 font-medium text-gray-900">
        {toolCall.name}
      </div>
      {toolPath && (
        <div className="mt-4 text-12 text-gray-600">{toolPath}</div>
      )}

      <label className="mt-12 flex items-center gap-8 text-12 text-gray-700">
        <input
          type="checkbox"
          checked={remember}
          onChange={(event) => setRemember(event.target.checked)}
          aria-label="Always allow this tool"
          className="rounded-4"
        />
        <span>Always allow this tool</span>
      </label>

      <div className="mt-12 flex gap-8">
        <button
          type="button"
          onClick={() => onApprove(remember)}
          className="rounded-6 bg-green-600 px-12 py-6 text-12 font-medium text-white hover:bg-green-700"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={onReject}
          className="rounded-6 border border-red-300 px-12 py-6 text-12 font-medium text-red-600 hover:bg-red-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
});
