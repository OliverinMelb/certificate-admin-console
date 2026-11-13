import { createRunner, prepare, backend, python, root } from './runtime.mjs'

const runner = createRunner()
try {
  await prepare(runner)
  await runner.npm(['run', 'typecheck'])
  await runner.npm(['run', 'build'])
  await runner.run('HTTP contracts', python, ['-m', 'pytest', '-q'], backend)
  await runner.run('Real startup smoke', python, ['-m', 'pytest', 'tests', '-q'], root)
} catch (error) {
  console.error(error.message)
  process.exitCode = runner.stopped ? 130 : 1
} finally {
  runner.dispose()
}
