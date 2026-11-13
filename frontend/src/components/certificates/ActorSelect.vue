<script setup lang="ts">
import type { Actor, Course } from '../../api/certificates'
defineProps<{ actors: readonly Actor[]; actorId: string; loading: boolean; error: string; courses: readonly Course[]; coursesLoading: boolean; coursesError: string }>()
const emit = defineEmits<{ select: [id: string]; retryActors: []; retryCourses: [] }>()
</script>

<template>
  <section class="identity panel" aria-labelledby="identity-title">
    <div>
      <h2 id="identity-title" class="section-title">工作空间</h2>
      <p class="muted">演示身份 · 仅查看所属租户的数据</p>
      <label class="field">演示管理员
        <select :value="actorId" :disabled="loading || !actors.length" @change="emit('select', ($event.target as HTMLSelectElement).value)">
          <option v-if="!actors.length" value="">暂无可用身份</option>
          <option v-for="item in actors" :key="item.id" :value="item.id">{{ item.email }} · {{ item.tenant_name }}</option>
        </select>
      </label>
      <p v-if="loading" role="status">正在加载演示身份…</p>
      <p v-else-if="error" role="alert" class="error">{{ error }} <button type="button" @click="emit('retryActors')">重试身份</button></p>
      <p v-else-if="!actors.length" role="status" class="muted">暂无演示身份。<button type="button" @click="emit('retryActors')">重新加载身份</button></p>
    </div>
    <div class="courses">
      <h3 class="course-title">当前租户课程</h3>
      <p v-if="coursesLoading" role="status">正在加载课程…</p>
      <p v-else-if="coursesError" role="alert" class="error">{{ coursesError }} <button type="button" @click="emit('retryCourses')">重试课程</button></p>
      <ul v-else-if="courses.length" class="course-list"><li v-for="course in courses" :key="course.id" class="course">{{ course.title }}</li></ul>
      <p v-else class="muted">{{ actorId ? '暂无课程' : '请选择演示身份' }}</p>
    </div>
  </section>
</template>

<style scoped>
.identity { display: grid; grid-template-columns: minmax(0, 1fr) minmax(220px, 1fr); gap: 32px; }
.courses { border-left: 1px solid #e1e8ee; padding-left: 32px; }
.course-title { font-size: 14px; margin: 4px 0 12px; }
.course-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px; }
.course { background: #edf5f6; color: #245a60; border-radius: 6px; padding: 6px 12px; }
@media (max-width: 650px) { .identity { grid-template-columns: 1fr; gap: 20px; } .courses { border-left: 0; border-top: 1px solid #e1e8ee; padding: 16px 0 0; } }
</style>
