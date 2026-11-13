<script setup lang="ts">
import { reactive } from 'vue'
import { useCertificates } from '../../composables/useCertificates'
import ActorSelect from './ActorSelect.vue'
import CertificateFilters from './CertificateFilters.vue'
import CertificateTable from './CertificateTable.vue'
import CertificatePagination from './CertificatePagination.vue'
import CertificateDetail from './CertificateDetail.vue'

const state = reactive(useCertificates())
</script>

<template>
  <div class="certificate-page">
    <ActorSelect :actors="state.actors.data.items" :actor-id="state.actorId" :loading="state.actors.loading" :error="state.actors.error"
      :courses="state.courses.data.items" :courses-loading="state.courses.loading" :courses-error="state.courses.error"
      @select="state.selectActor" @retry-actors="state.loadActors" @retry-courses="state.loadCourses" />
    <section class="panel" aria-labelledby="certificates-title">
      <div class="list-heading"><h2 id="certificates-title" class="section-title">已颁发证书</h2><span v-if="state.actor" class="tenant">{{ state.actor.tenant_name }}</span></div>
      <p class="muted">浏览学员证书与颁发记录。所有颁发时间均以 UTC 显示。</p>
      <CertificateFilters :query="state.query" :sort="state.sort" :order="state.order" :disabled="!state.actorId"
        @search="state.search" @sort="state.changeSort" @order="state.changeOrder" />
      <CertificateTable :items="state.certificates.data.items" :loading="state.busy" :error="state.certificates.error" :has-actor="!!state.actorId"
        @detail="state.openDetail" @retry="state.loadList" />
      <CertificatePagination :page="state.page" :page-size="state.pageSize" :total="state.certificates.data.total"
        :disabled="state.busy" :unavailable="!state.actorId || !!state.certificates.error" @page="state.changePage" @page-size="state.changePageSize" />
    </section>
    <CertificateDetail v-if="state.detailId" :item="state.detail.data" :loading="state.detail.loading" :error="state.detail.error"
      @close="state.closeDetail" @retry="state.openDetail(state.detailId)" />
  </div>
</template>

<style scoped>
.certificate-page { display: grid; gap: 24px; }
.list-heading { display: flex; align-items: center; gap: 12px; }
.tenant { color: #245a60; background: #edf5f6; font-size: 12px; border-radius: 6px; padding: 2px 10px; }
</style>
