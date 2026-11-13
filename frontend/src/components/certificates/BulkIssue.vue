<script setup lang="ts">
import { reactive, shallowRef, watch } from 'vue'
import type { Course } from '../../api/certificates'
import { issueReason } from '../../api/issuance'
import { useBulkIssue } from '../../composables/useBulkIssue'

const props = defineProps<{ actorId: string; courses: readonly Course[] }>()
const emit = defineEmits<{ issued: [] }>()
const courseId = shallowRef('')
const state = reactive(useBulkIssue(() => props.actorId, () => emit('issued')))
watch(() => props.actorId, () => { courseId.value = '' }, { flush: 'sync' })
watch(() => props.courses, (courses) => {
  if (!courses.some((course) => course.id === courseId.value)) courseId.value = courses[0]?.id ?? ''
}, { immediate: true })
watch(courseId, () => state.clear(), { flush: 'sync' })

function changeCourse(event: Event) {
  courseId.value = (event.target as HTMLSelectElement).value
  state.clear()
}
</script>

<template>
  <section class="panel" aria-labelledby="issue-title" :aria-busy="state.busy">
    <h2 id="issue-title" class="section-title">批量发证</h2>
    <p class="muted">为完成课程且从未获证的学员发证；已有证书（含已撤销）会跳过。</p>
    <form class="issue-form" @submit.prevent="state.submit(courseId)">
      <label class="field">发证课程
        <select :value="courseId" :disabled="state.busy || !actorId || !courses.length" @change="changeCourse">
          <option v-if="!courses.length" value="">暂无可选课程</option>
          <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.title }}</option>
        </select>
      </label>
      <button type="submit" :disabled="state.busy || !actorId || !courseId">{{ state.busy ? '正在发证…' : state.result || state.error ? '重新发起发证' : '批量发证' }}</button>
      <button v-if="state.canRetry" type="button" @click="state.retry()">重试原操作</button>
    </form>
    <p v-if="state.busy" role="status">正在处理课程报名，请等待结果。</p>
    <p v-if="state.error" role="alert" class="error">{{ state.error }}</p>
    <p v-if="state.canRetry" class="muted">重试原操作会获取首次结果；重新发起发证会再次检查当前课程的报名。</p>
    <div v-if="state.result" class="outcomes">
      <p role="status">处理完成，共 {{ state.result.outcomes.length }} 名学员。</p>
      <p v-if="!state.result.outcomes.length" class="muted">此课程暂无报名学员。</p>
      <ul v-else aria-label="逐学员发证结果">
        <li v-for="outcome in state.result.outcomes" :key="outcome.learner_id">
          <strong>{{ outcome.learner_id }}</strong>
          <span>{{ outcome.outcome }} · {{ issueReason(outcome.reason) }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.issue-form { display: flex; align-items: end; flex-wrap: wrap; gap: 16px; }
.outcomes ul { list-style: none; margin: 0; padding: 0; max-height: 280px; overflow-y: auto; }
.outcomes li { display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 0; border-bottom: 1px solid #e6edf1; font-size: 13px; }
.outcomes strong { min-width: 160px; }
</style>
