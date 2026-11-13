import { createRunner, prepare, backend, python } from './runtime.mjs'

const runner = createRunner()
try {
  const args = process.argv.slice(2)
  if (args.length && (args.length !== 2 || args[0] !== '--port' || !/^\d+$/.test(args[1]))) {
    throw new Error('Usage: node scripts/start.mjs [--port 8000]')
  }
  const port = Number(args[1] ?? 8000)
  if (port < 1 || port > 65535) throw new Error('Port must be between 1 and 65535.')
  await prepare(runner)
  await runner.npm(['run', 'typecheck'])
  await runner.npm(['run', 'build'])
  console.log(`Opening service at http://127.0.0.1:${port} (Ctrl+C to stop)`)
  await runner.run('Start application', python, ['-m', 'app.serve', '--port', String(port)], backend)
} catch (error) {
  console.error(error.message)
  process.exitCode = runner.stopped ? 130 : 1
} finally {
  runner.dispose()
}
