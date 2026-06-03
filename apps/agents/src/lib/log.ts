/**
 * Minimal structured logger.
 * Swap for pino/winston later if needed - the API stays the same.
 */

type Level = 'debug' | 'info' | 'warn' | 'error';

function emit(level: Level, msg: string, ctx?: unknown) {
  const line = {
    t: new Date().toISOString(),
    level,
    msg,
    ...(ctx ? { ctx } : {}),
  };
  const text = JSON.stringify(line);
  if (level === 'error') console.error(text);
  else if (level === 'warn') console.warn(text);
  else console.log(text);
}

export const log = {
  debug: (msg: string, ctx?: unknown) => emit('debug', msg, ctx),
  info: (msg: string, ctx?: unknown) => emit('info', msg, ctx),
  warn: (msg: string, ctx?: unknown) => emit('warn', msg, ctx),
  error: (msg: string, ctx?: unknown) => {
    if (ctx instanceof Error) {
      emit('error', msg, { message: ctx.message, stack: ctx.stack });
    } else {
      emit('error', msg, ctx);
    }
  },
};
