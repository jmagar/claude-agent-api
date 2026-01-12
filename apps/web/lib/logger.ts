/**
 * Structured logging utilities with correlation ID support
 */

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogContext {
  correlationId?: string;
  userId?: string;
  sessionId?: string;
  [key: string]: unknown;
}

function formatTimestamp(date: Date): string {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const parts = formatter.formatToParts(date);
  const lookup = parts.reduce<Record<string, string>>((acc, part) => {
    if (part.type !== "literal") {
      acc[part.type] = part.value;
    }
    return acc;
  }, {});

  return `${lookup.hour}:${lookup.minute}:${lookup.second} | ${lookup.month}/${lookup.day}/${lookup.year}`;
}

class Logger {
  private context: LogContext = {};

  setContext(context: LogContext): void {
    this.context = { ...this.context, ...context };
  }

  clearContext(): void {
    this.context = {};
  }

  private log(level: LogLevel, message: string, extra?: Record<string, unknown>): void {
    const timestamp = formatTimestamp(new Date());
    const logData = {
      timestamp,
      level,
      message,
      ...this.context,
      ...extra,
    };

    const method = level === "error" ? "error" : level === "warn" ? "warn" : "log";
    console[method](JSON.stringify(logData));
  }

  debug(message: string, extra?: Record<string, unknown>): void {
    if (process.env.NODE_ENV === "development") {
      this.log("debug", message, extra);
    }
  }

  info(message: string, extra?: Record<string, unknown>): void {
    this.log("info", message, extra);
  }

  warn(message: string, extra?: Record<string, unknown>): void {
    this.log("warn", message, extra);
  }

  error(message: string, error?: Error, extra?: Record<string, unknown>): void {
    this.log("error", message, {
      ...extra,
      error: error
        ? {
            name: error.name,
            message: error.message,
            stack: error.stack,
          }
        : undefined,
    });
  }
}

export const logger = new Logger();
