<script setup lang="ts">
import ServiceStatus from './components/ServiceStatus.vue'
import CertificatePage from './components/certificates/CertificatePage.vue'
</script>

<template>
  <main class="shell">
    <p class="eyebrow">CERTIFICATE ADMIN CONSOLE</p>
    <h1 class="title">证书管理后台</h1>
    <p class="intro">管理培训证书，让每一次学习成果都有据可查。</p>
    <CertificatePage />
    <div class="connection"><ServiceStatus /></div>
  </main>
</template>

<style scoped>
.shell { max-width: 1240px; margin: 40px auto; padding: 24px; }
.eyebrow { color: #526c80; font-size: 12px; font-weight: 700; letter-spacing: 0.14em; }
.title { font-size: clamp(28px, 5vw, 40px); margin-bottom: 8px; }
.intro { color: #526575; margin-bottom: 32px; }
.connection { margin-top: 24px; }
</style>
