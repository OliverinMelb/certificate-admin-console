import { spawn } from 'node:child_process'
import { existsSync, realpathSync } from 'node:fs'
import { delimiter, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
export const frontend = join(root, 'frontend')
export const backend = join(root, 'backend')
export const python = join(backend, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')

function npmCli() {
  for (const directory of [dirname(process.execPath), ...(process.env.PATH ?? '').split(delimiter)]) {
    for (const candidate of [join(directory, 'node_modules/npm/bin/npm-cli.js'), join(directory, '../lib/node_modules/npm/bin/npm-cli.js')]) {
      if (existsSync(candidate)) return candidate
    }
    const binary = join(directory, 'npm')
    if (existsSync(binary) && process.platform !== 'win32') return realpathSync(binary)
  }
  throw new Error('npm is required. Install Node.js 24 with npm and retry.')
}

export function createRunner() {
  let active
  let stopping = false
  let forceTimer
  let killTimer

  function stop() {
    if (stopping) return
    stopping = true
    if (!active) return
    const child = active
    // EOF tells the server to finish gracefully, also when the launcher disappears.
    child.stdin?.end()
    forceTimer = setTimeout(() => {
      if (child.exitCode !== null || child.signalCode !== null) return
      if (process.platform === 'win32') {
        spawn('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' })
      } else {
        try { process.kill(-child.pid, 'SIGTERM') } catch { /* Already exited. */ }
        killTimer = setTimeout(() => {
          if (child.exitCode === null && child.signalCode === null) {
            try { process.kill(-child.pid, 'SIGKILL') } catch { /* Already exited. */ }
          }
        }, 2000)
      }
    }, 2000)
  }

  const signals = ['SIGINT', 'SIGTERM', ...(process.platform === 'win32' ? ['SIGBREAK'] : ['SIGHUP'])]
  for (const signal of signals) process.on(signal, stop)

  async function run(label, command, args, cwd = root) {
    if (stopping) throw new Error('Stopped by user')
    console.log(`[${label}]`)
    return new Promise((resolveStep, reject) => {
      const child = spawn(command, args, {
        cwd, shell: false, windowsHide: true, detached: process.platform !== 'win32',
        stdio: ['pipe', 'inherit', 'inherit'],
        env: { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8', UV_PYTHON_DOWNLOADS: 'never' },
      })
      active = child
      child.stdin.on('error', () => {}) // Child may exit while shutdown closes stdin.
      child.once('error', error => reject(new Error(`${label}: ${error.message}`)))
      child.once('close', (code, signal) => {
        active = undefined
        clearTimeout(forceTimer)
        clearTimeout(killTimer)
        if (stopping) reject(new Error('Stopped by user'))
        else if (code === 0) resolveStep()
        else reject(new Error(`${label} failed (exit ${code ?? signal}).`))
      })
    })
  }

  return {
    run,
    npm: (args) => run(`npm ${args.join(' ')}`, process.execPath, [npmCli(), ...args], frontend),
    get stopped() { return stopping },
    dispose() { for (const signal of signals) process.off(signal, stop) },
  }
}

export async function prepare(runner) {
  if (Number(process.versions.node.split('.')[0]) !== 24) throw new Error('Node.js 24 is required.')
  await runner.run('Check uv', 'uv', ['--version'])
  await runner.npm(['--version'])
  await runner.run('Sync Python dependencies', 'uv', ['sync', '--locked'], backend)
  await runner.npm(['ci', '--no-audit', '--no-fund'])
}
