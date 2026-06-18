<template>
  <div class="page-card gantt-page">
    <div class="gantt-header">
      <div class="header-left">
        <div class="page-title">甘特图</div>
        <n-select
          v-model:value="selectedProjectId"
          placeholder="选择项目"
          :options="projectOptions"
          style="width: 240px"
          @update:value="handleProjectChange"
        />
      </div>
      <div class="header-right">
        <n-radio-group v-model:value="viewMode" size="small">
          <n-radio-button value="day">按天</n-radio-button>
          <n-radio-button value="week">按周</n-radio-button>
          <n-radio-button value="month">按月</n-radio-button>
        </n-radio-group>
      </div>
    </div>

    <div v-if="!selectedProjectId" class="empty-state">
      <n-empty description="请先选择一个项目" />
    </div>

    <div v-else class="gantt-container">
      <div class="gantt-body">
        <div class="task-list-panel">
          <div class="task-list-header">任务名称</div>
          <div class="task-list-content" ref="taskListContentRef" @scroll="handleTaskListScroll">
            <div
              v-for="task in flatTasks"
              :key="task.id"
              class="task-row"
              :style="{ paddingLeft: task.level * 20 + 10 + 'px', height: rowHeight + 'px' }"
            >
              <span
                v-if="task.children && task.children.length > 0"
                class="collapse-icon"
                @click="toggleCollapse(task.id)"
              >
                <n-icon size="14">
                  <ChevronDownOutline v-if="!collapsedTasks.has(task.id)" />
                  <ChevronForwardOutline v-else />
                </n-icon>
              </span>
              <span v-else class="collapse-placeholder"></span>
              <span class="task-name">{{ task.title }}</span>
            </div>
          </div>
        </div>

        <div class="timeline-panel" ref="timelinePanelRef">
          <div class="timeline-header" ref="timelineHeaderRef">
            <div class="timeline-scale-top" :style="{ width: timelineWidth + 'px' }">
              <div
                v-for="(item, index) in topScaleItems"
                :key="'top-' + index"
                class="scale-item-top"
                :style="{ width: item.width + 'px', left: item.left + 'px' }"
              >
                {{ item.label }}
              </div>
            </div>
            <div class="timeline-scale-bottom" :style="{ width: timelineWidth + 'px' }">
              <div
                v-for="(item, index) in bottomScaleItems"
                :key="'bottom-' + index"
                class="scale-item-bottom"
                :style="{ width: item.width + 'px', left: item.left + 'px' }"
              >
                {{ item.label }}
              </div>
            </div>
          </div>

          <div class="timeline-content" ref="timelineContentRef" @scroll="handleTimelineScroll">
            <svg
              class="dependency-svg"
              :width="timelineWidth"
              :height="timelineHeight"
              :viewBox="`0 0 ${timelineWidth} ${timelineHeight}`"
            >
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
                </marker>
              </defs>
              <path
                v-for="(dep, index) in dependencyPaths"
                :key="'dep-' + index"
                :d="dep.path"
                stroke="#94a3b8"
                stroke-width="1.5"
                fill="none"
                marker-end="url(#arrowhead)"
              />
            </svg>

            <div class="grid-lines" :style="{ width: timelineWidth + 'px', height: timelineHeight + 'px' }">
              <div
                v-for="(item, index) in bottomScaleItems"
                :key="'grid-' + index"
                class="grid-line"
                :style="{ left: item.left + 'px', height: timelineHeight + 'px' }"
              ></div>
            </div>

            <div class="milestone-layer" :style="{ width: timelineWidth + 'px', height: timelineHeight + 'px' }">
              <div
                v-for="milestone in milestones"
                :key="'milestone-' + milestone.id"
                class="milestone-item"
                :style="{
                  left: getDatePosition(milestone.date) + 'px',
                  top: 0,
                  height: timelineHeight + 'px',
                }"
                :title="milestone.title"
              >
                <div class="milestone-diamond">
                  <n-icon size="14" color="#f59e0b"><FlagOutline /></n-icon>
                </div>
                <div class="milestone-label">{{ milestone.title }}</div>
              </div>
            </div>

            <div class="task-bars-layer" :style="{ width: timelineWidth + 'px', height: timelineHeight + 'px' }">
              <div
                v-for="task in flatTasks"
                :key="'bar-' + task.id"
                class="task-bar-row"
                :style="{ top: getTaskTop(task) + 'px', height: rowHeight + 'px' }"
              >
                <div
                  v-if="task.start_date && task.due_date"
                  class="task-bar"
                  :class="{ 'task-bar-dragging': draggingTask?.id === task.id }"
                  :style="{
                    left: getDatePosition(task.start_date) + 'px',
                    width: getTaskWidth(task) + 'px',
                    backgroundColor: getTaskColor(task),
                  }"
                  @mousedown="handleBarMouseDown($event, task, 'move')"
                >
                  <div
                    class="resize-handle resize-handle-left"
                    @mousedown.stop="handleBarMouseDown($event, task, 'left')"
                  ></div>
                  <div class="task-bar-content">
                    <span class="task-bar-title">{{ task.title }}</span>
                  </div>
                  <div
                    class="resize-handle resize-handle-right"
                    @mousedown.stop="handleBarMouseDown($event, task, 'right')"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="gantt-footer">
        <n-button type="primary" size="small" @click="showCreateMilestone = true">
          <template #icon>
            <n-icon><FlagOutline /></n-icon>
          </template>
          新建里程碑
        </n-button>
      </div>
    </div>

    <n-modal v-model:show="showCreateMilestone" preset="card" title="新建里程碑" style="width: 420px">
      <n-form ref="milestoneFormRef" :model="milestoneForm" label-placement="top">
        <n-form-item label="里程碑名称" path="title" :rule="{ required: true, message: '请输入里程碑名称' }">
          <n-input v-model:value="milestoneForm.title" placeholder="请输入里程碑名称" />
        </n-form-item>
        <n-form-item label="日期" path="date" :rule="{ required: true, message: '请选择日期' }">
          <n-date-picker v-model:value="milestoneForm.date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="milestoneForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateMilestone = false">取消</n-button>
          <n-button type="primary" :loading="creatingMilestone" @click="handleCreateMilestone">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useApi } from '../../utils/request'
import {
  listProjectsApi,
  listTasksApi,
  updateTaskApi,
  listMilestonesApi,
  createMilestoneApi,
} from '../../api/project'
import {
  ChevronDownOutline,
  ChevronForwardOutline,
  FlagOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const { message, handleError } = useApi()

const projects = ref([])
const selectedProjectId = ref(null)
const viewMode = ref('day')
const tasks = ref([])
const milestones = ref([])
const collapsedTasks = ref(new Set())

const taskListContentRef = ref(null)
const timelineContentRef = ref(null)
const timelineHeaderRef = ref(null)
const rowHeight = 40
const baseCellWidth = 60

const showCreateMilestone = ref(false)
const milestoneFormRef = ref(null)
const creatingMilestone = ref(false)
const milestoneForm = reactive({
  title: '',
  date: null,
  description: '',
})

const draggingTask = ref(null)
const dragType = ref(null)
const dragStartX = ref(0)
const dragStartStartDate = ref(null)
const dragStartDueDate = ref(null)
let isScrolling = false

const projectOptions = computed(() => {
  return projects.value.map((p) => ({ label: p.name, value: p.id }))
})

const dayWidth = computed(() => {
  switch (viewMode.value) {
    case 'day': return 60
    case 'week': return 24
    case 'month': return 10
    default: return 60
  }
})

const cellWidth = computed(() => {
  if (viewMode.value === 'day') return dayWidth.value
  if (viewMode.value === 'week') return dayWidth.value * 7
  return dayWidth.value * 30
})

const dateRange = computed(() => {
  if (!selectedProjectId.value || flatTasks.value.length === 0) {
    const today = new Date()
    const start = new Date(today)
    start.setDate(start.getDate() - 7)
    const end = new Date(today)
    end.setDate(end.getDate() + 30)
    return { start, end }
  }

  let minDate = null
  let maxDate = null

  flatTasks.value.forEach((task) => {
    if (task.start_date) {
      const d = new Date(task.start_date)
      if (!minDate || d < minDate) minDate = d
    }
    if (task.due_date) {
      const d = new Date(task.due_date)
      if (!maxDate || d > maxDate) maxDate = d
    }
  })

  milestones.value.forEach((m) => {
    const d = new Date(m.date)
    if (!minDate || d < minDate) minDate = d
    if (!maxDate || d > maxDate) maxDate = d
  })

  if (!minDate) minDate = new Date()
  if (!maxDate) maxDate = new Date()

  const start = new Date(minDate)
  start.setDate(start.getDate() - 7)
  const end = new Date(maxDate)
  end.setDate(end.getDate() + 7)

  return { start, end }
})

const totalDays = computed(() => {
  const { start, end } = dateRange.value
  return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
})

const timelineWidth = computed(() => {
  return totalDays.value * dayWidth.value
})

const timelineHeight = computed(() => {
  return flatTasks.value.length * rowHeight
})

const topScaleItems = computed(() => {
  const items = []
  const { start, end } = dateRange.value

  if (viewMode.value === 'day' || viewMode.value === 'week') {
    let current = new Date(start.getFullYear(), start.getMonth(), 1)
    while (current <= end) {
      const monthStart = new Date(current)
      const nextMonth = new Date(current.getFullYear(), current.getMonth() + 1, 1)
      const monthEnd = new Date(Math.min(nextMonth.getTime(), end.getTime()))
      
      const left = (monthStart - start) / (1000 * 60 * 60 * 24) * dayWidth.value
      const width = (monthEnd - monthStart) / (1000 * 60 * 60 * 24) * dayWidth.value
      
      items.push({
        label: `${current.getFullYear()}年${current.getMonth() + 1}月`,
        left,
        width,
      })
      
      current.setMonth(current.getMonth() + 1)
    }
  } else {
    let current = new Date(start.getFullYear(), 0, 1)
    while (current <= end) {
      const yearStart = new Date(current)
      const nextYear = new Date(current.getFullYear() + 1, 0, 1)
      const yearEnd = new Date(Math.min(nextYear.getTime(), end.getTime()))
      
      const left = (yearStart - start) / (1000 * 60 * 60 * 24) * dayWidth.value
      const width = (yearEnd - yearStart) / (1000 * 60 * 60 * 24) * dayWidth.value
      
      items.push({
        label: `${current.getFullYear()}年`,
        left,
        width,
      })
      
      current.setFullYear(current.getFullYear() + 1)
    }
  }

  return items
})

const bottomScaleItems = computed(() => {
  const items = []
  const { start, end } = dateRange.value

  if (viewMode.value === 'day') {
    const current = new Date(start)
    current.setHours(0, 0, 0, 0)
    let index = 0
    while (current <= end) {
      items.push({
        label: current.getDate(),
        left: index * dayWidth.value,
        width: dayWidth.value,
      })
      current.setDate(current.getDate() + 1)
      index++
    }
  } else if (viewMode.value === 'week') {
    const current = new Date(start)
    current.setHours(0, 0, 0, 0)
    const dayOfWeek = current.getDay()
    current.setDate(current.getDate() - dayOfWeek)
    
    let weekNum = 1
    while (current <= end) {
      const weekStart = new Date(Math.max(current.getTime(), start.getTime()))
      const weekEnd = new Date(current)
      weekEnd.setDate(weekEnd.getDate() + 7)
      const actualEnd = new Date(Math.min(weekEnd.getTime(), end.getTime()))
      
      const left = (weekStart - start) / (1000 * 60 * 60 * 24) * dayWidth.value
      const width = (actualEnd - weekStart) / (1000 * 60 * 60 * 24) * dayWidth.value
      
      const monthStart = new Date(start.getFullYear(), start.getMonth(), 1)
      const weekOfMonth = Math.ceil((current - monthStart) / (7 * 24 * 60 * 60 * 1000))
      
      items.push({
        label: `第${weekOfMonth}周`,
        left,
        width,
      })
      
      current.setDate(current.getDate() + 7)
      weekNum++
    }
  } else {
    const current = new Date(start.getFullYear(), start.getMonth(), 1)
    while (current <= end) {
      const monthStart = new Date(Math.max(current.getTime(), start.getTime()))
      const nextMonth = new Date(current.getFullYear(), current.getMonth() + 1, 1)
      const monthEnd = new Date(Math.min(nextMonth.getTime(), end.getTime()))
      
      const left = (monthStart - start) / (1000 * 60 * 60 * 24) * dayWidth.value
      const width = (monthEnd - monthStart) / (1000 * 60 * 60 * 24) * dayWidth.value
      
      items.push({
        label: `${current.getMonth() + 1}月`,
        left,
        width,
      })
      
      current.setMonth(current.getMonth() + 1)
    }
  }

  return items
})

const flatTasks = computed(() => {
  const result = []

  function flatten(taskList, level) {
    taskList.forEach((task) => {
      result.push({ ...task, level })
      if (task.children && task.children.length > 0 && !collapsedTasks.value.has(task.id)) {
        flatten(task.children, level + 1)
      }
    })
  }

  flatten(tasks.value, 0)
  return result
})

const dependencyPaths = computed(() => {
  const paths = []
  const taskMap = new Map()

  flatTasks.value.forEach((task, index) => {
    taskMap.set(task.id, { task, index })
  })

  flatTasks.value.forEach((task) => {
    if (task.dependencies && task.dependencies.length > 0) {
      task.dependencies.forEach((depId) => {
        const depTaskInfo = taskMap.get(depId)
        if (depTaskInfo && task.start_date && task.due_date && depTaskInfo.task.start_date && depTaskInfo.task.due_date) {
          const fromX = getDatePosition(depTaskInfo.task.due_date)
          const fromY = depTaskInfo.index * rowHeight + rowHeight / 2
          const toX = getDatePosition(task.start_date)
          const toY = taskMap.get(task.id).index * rowHeight + rowHeight / 2

          const midX = (fromX + toX) / 2
          const path = `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`
          paths.push({ path })
        }
      })
    }
  })

  return paths
})

function getDatePosition(dateStr) {
  if (!dateStr) return 0
  const date = new Date(dateStr)
  const { start } = dateRange.value
  const diff = (date - start) / (1000 * 60 * 60 * 24)
  return diff * dayWidth.value
}

function getTaskWidth(task) {
  if (!task.start_date || !task.due_date) return 0
  const start = new Date(task.start_date)
  const end = new Date(task.due_date)
  const diff = (end - start) / (1000 * 60 * 60 * 24)
  return Math.max(diff * dayWidth.value, dayWidth.value * 0.5)
}

function getTaskTop(task) {
  const index = flatTasks.value.findIndex((t) => t.id === task.id)
  return index * rowHeight
}

function getTaskColor(task) {
  const statusColors = {
    todo: '#94a3b8',
    in_progress: '#3b82f6',
    done: '#10b981',
  }
  return statusColors[task.status] || '#94a3b8'
}

function toggleCollapse(taskId) {
  const newSet = new Set(collapsedTasks.value)
  if (newSet.has(taskId)) {
    newSet.delete(taskId)
  } else {
    newSet.add(taskId)
  }
  collapsedTasks.value = newSet
}

function handleTaskListScroll(e) {
  if (isScrolling) return
  isScrolling = true
  if (timelineContentRef.value) {
    timelineContentRef.value.scrollTop = e.target.scrollTop
  }
  requestAnimationFrame(() => {
    isScrolling = false
  })
}

function handleTimelineScroll(e) {
  if (timelineHeaderRef.value) {
    timelineHeaderRef.value.scrollLeft = e.target.scrollLeft
  }
  if (isScrolling) return
  isScrolling = true
  if (taskListContentRef.value) {
    taskListContentRef.value.scrollTop = e.target.scrollTop
  }
  requestAnimationFrame(() => {
    isScrolling = false
  })
}

function handleBarMouseDown(e, task, type) {
  e.preventDefault()
  if (!task.start_date || !task.due_date) return
  
  draggingTask.value = task
  dragType.value = type
  dragStartX.value = e.clientX
  dragStartStartDate.value = new Date(task.start_date)
  dragStartDueDate.value = new Date(task.due_date)

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(e) {
  if (!draggingTask.value) return

  const deltaX = e.clientX - dragStartX.value
  const deltaDays = deltaX / dayWidth.value

  const task = draggingTask.value

  if (dragType.value === 'move') {
    if (dragStartStartDate.value && dragStartDueDate.value) {
      const newStart = new Date(dragStartStartDate.value)
      newStart.setDate(newStart.getDate() + Math.round(deltaDays))
      const newDue = new Date(dragStartDueDate.value)
      newDue.setDate(newDue.getDate() + Math.round(deltaDays))

      task.start_date = newStart.toISOString()
      task.due_date = newDue.toISOString()
    }
  } else if (dragType.value === 'left') {
    if (dragStartStartDate.value) {
      const newStart = new Date(dragStartStartDate.value)
      newStart.setDate(newStart.getDate() + Math.round(deltaDays))
      const dueDate = new Date(task.due_date)
      if (newStart < dueDate) {
        task.start_date = newStart.toISOString()
      }
    }
  } else if (dragType.value === 'right') {
    if (dragStartDueDate.value) {
      const newDue = new Date(dragStartDueDate.value)
      newDue.setDate(newDue.getDate() + Math.round(deltaDays))
      const startDate = new Date(task.start_date)
      if (newDue > startDate) {
        task.due_date = newDue.toISOString()
      }
    }
  }
}

async function handleMouseUp() {
  if (draggingTask.value) {
    try {
      await updateTaskApi(draggingTask.value.id, {
        start_date: draggingTask.value.start_date,
        due_date: draggingTask.value.due_date,
      })
      message.success('日期已更新')
    } catch (e) {
      handleError(e, '更新失败')
    }
  }

  draggingTask.value = null
  dragType.value = null
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

async function fetchProjects() {
  try {
    const res = await listProjectsApi()
    projects.value = res
    if (res.length > 0 && !selectedProjectId.value) {
      selectedProjectId.value = res[0].id
      await nextTick()
      await fetchTasks()
      await fetchMilestones()
    }
  } catch (e) {
    handleError(e, '获取项目列表失败')
  }
}

async function fetchTasks() {
  if (!selectedProjectId.value) return
  try {
    const res = await listTasksApi(selectedProjectId.value)
    tasks.value = res
  } catch (e) {
    handleError(e, '获取任务列表失败')
  }
}

async function fetchMilestones() {
  if (!selectedProjectId.value) return
  try {
    const res = await listMilestonesApi(selectedProjectId.value)
    milestones.value = res
  } catch (e) {
    handleError(e, '获取里程碑失败')
  }
}

async function handleProjectChange() {
  await fetchTasks()
  await fetchMilestones()
}

async function handleCreateMilestone() {
  try {
    await milestoneFormRef.value?.validate()
  } catch (e) {
    return
  }
  creatingMilestone.value = true
  try {
    await createMilestoneApi(selectedProjectId.value, milestoneForm)
    message.success('创建成功')
    showCreateMilestone.value = false
    milestoneForm.title = ''
    milestoneForm.date = null
    milestoneForm.description = ''
    await fetchMilestones()
  } catch (e) {
    handleError(e, '创建失败')
  } finally {
    creatingMilestone.value = false
  }
}

onMounted(async () => {
  await fetchProjects()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style lang="scss" scoped>
.gantt-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 500px;
}

.gantt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gantt-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.gantt-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.task-list-panel {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  background: #f8fafc;

  .task-list-header {
    height: 61px;
    line-height: 61px;
    padding: 0 12px;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
    border-bottom: 1px solid #e2e8f0;
    background: #f1f5f9;
    flex-shrink: 0;
  }

  .task-list-content {
    flex: 1;
    overflow-y: scroll;
    overflow-x: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;

    &::-webkit-scrollbar {
      display: none;
    }
  }

  .task-row {
    display: flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 13px;
    color: #334155;
    box-sizing: border-box;
    cursor: pointer;
    transition: background 0.15s;

    &:hover {
      background: #f1f5f9;
    }
  }

  .collapse-icon {
    cursor: pointer;
    color: #64748b;
    display: flex;
    align-items: center;
    width: 16px;
    flex-shrink: 0;
    transition: color 0.2s;

    &:hover {
      color: #3b82f6;
    }
  }

  .collapse-placeholder {
    width: 16px;
    flex-shrink: 0;
  }

  .task-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.timeline-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;

  .timeline-header {
    height: 61px;
    flex-shrink: 0;
    background: #f1f5f9;
    border-bottom: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
    z-index: 10;

    .timeline-scale-top {
      height: 30px;
      position: relative;
      border-bottom: 1px solid #e2e8f0;

      .scale-item-top {
        position: absolute;
        top: 0;
        height: 30px;
        line-height: 30px;
        text-align: center;
        font-size: 12px;
        font-weight: 600;
        color: #475569;
        border-right: 1px solid #e2e8f0;
        box-sizing: border-box;
      }
    }

    .timeline-scale-bottom {
      height: 30px;
      position: relative;

      .scale-item-bottom {
        position: absolute;
        top: 0;
        height: 30px;
        line-height: 30px;
        text-align: center;
        font-size: 11px;
        color: #64748b;
        border-right: 1px solid #e2e8f0;
        box-sizing: border-box;
      }
    }
  }

  .timeline-content {
    flex: 1;
    overflow: auto;
    position: relative;
    background: #ffffff;
  }

  .dependency-svg {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 1;
  }

  .grid-lines {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;

    .grid-line {
      position: absolute;
      top: 0;
      width: 1px;
      background: #f1f5f9;
    }
  }

  .milestone-layer {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 3;

    .milestone-item {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      transform: translateX(-50%);

      .milestone-diamond {
        width: 22px;
        height: 22px;
        background: #fef3c7;
        border: 2px solid #f59e0b;
        transform: rotate(45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 10px;

        :deep(.n-icon) {
          transform: rotate(-45deg);
        }
      }

      .milestone-label {
        margin-top: 6px;
        font-size: 10px;
        color: #d97706;
        font-weight: 600;
        white-space: nowrap;
        writing-mode: vertical-lr;
        text-orientation: mixed;
      }
    }
  }

  .task-bars-layer {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 2;

    .task-bar-row {
      position: absolute;
      left: 0;
      right: 0;
    }
  }

  .task-bar {
    position: absolute;
    height: 24px;
    top: 8px;
    border-radius: 4px;
    cursor: move;
    display: flex;
    align-items: center;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
    transition: box-shadow 0.2s, transform 0.1s;
    user-select: none;
    min-width: 20px;

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      transform: translateY(-1px);
    }

    &.task-bar-dragging {
      opacity: 0.85;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
      z-index: 100;
    }

    .task-bar-content {
      flex: 1;
      padding: 0 8px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      font-size: 12px;
      color: #fff;
      font-weight: 500;
    }

    .resize-handle {
      width: 8px;
      height: 100%;
      cursor: ew-resize;
      flex-shrink: 0;
      transition: background 0.2s;

      &:hover {
        background: rgba(255, 255, 255, 0.3);
      }
    }

    .resize-handle-left {
      border-radius: 4px 0 0 4px;
    }

    .resize-handle-right {
      border-radius: 0 4px 4px 0;
    }
  }
}

.gantt-footer {
  padding: 12px 16px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}
</style>
