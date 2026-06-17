<template>
  <div class="page-card">
    <div class="page-title">日历视图</div>
    <n-calendar :default-value="calendarDefault" />
  </div>
</template>

<script setup>
const calendarDefault = new Date().getTime()
</script>
