/**
 * useAutocomplete hook tests
 */

import { render, act } from "@testing-library/react";
import { useAutocomplete } from "@/hooks/useAutocomplete";

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function HookHarness({ value, cursorPosition }: { value: string; cursorPosition: number }) {
  useAutocomplete({
    value,
    cursorPosition,
    debounceMs: 300,
  });
  return <div data-testid="autocomplete-harness" />;
}

describe("useAutocomplete", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("passes AbortController signal to fetch", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [] }),
    });

    const { unmount } = render(<HookHarness value="@agent" cursorPosition={6} />);

    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });

    const [, options] = mockFetch.mock.calls[0];
    expect(options).toEqual(expect.objectContaining({ signal: expect.any(AbortSignal) }));

    unmount();
  });

  it("aborts in-flight request when a new trigger arrives", async () => {
    const abortSpy = jest.fn();
    const originalAbortController = global.AbortController;

    global.AbortController = class MockAbortController {
      signal = {} as AbortSignal;
      abort = abortSpy;
    } as typeof AbortController;

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ items: [] }),
    });

    const { rerender, unmount } = render(<HookHarness value="@agent" cursorPosition={6} />);

    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });

    rerender(<HookHarness value="@tool" cursorPosition={5} />);

    await act(async () => {
      jest.advanceTimersByTime(350);
      await Promise.resolve();
    });

    expect(abortSpy).toHaveBeenCalled();

    global.AbortController = originalAbortController;
    unmount();
  });
});
