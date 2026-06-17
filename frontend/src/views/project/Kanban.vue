<template>
  <div class="page-card">
    <div class="page-header">
      <div class="page-title">项目看板</div>
      <n-button type="primary" @click="showCreateDrawer = true">
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        新建项目
      </n-button>
    </div>

    <n-grid :cols="3" :x-gap="20" :y-gap="20" v-if="projects.length > 0">
      <n-gi v-for="project in projects" :key="project.id">
        <n-card hoverable class="project-card" @click="goToProject(project.id)">
          <div class="project-cover" :style="{ backgroundColor: project.cover_color }">
            <span class="project-initials">{{ project.name.substring(0, 2) }}</span>
          </div>
          <div class="project-info">
            <div class="project-name">{{ project.name }}</div>
            <div class="project-desc" v-if="project.description">{{ project.description }}</div>
            <div class="project-desc empty" v-else>暂无描述</div>
            <div class="project-meta">
              <n-avatar-group>
                <n-avatar
                  v-for="(member, idx) in project.project_members.slice(0, 5)"
                  :key="member.id"
                  round
                  size="small"
                  :style="{ backgroundColor: avatarColors[idx % avatarColors.length] }"
                >
                  {{ member.user.name.charAt(0) }}
                </n-avatar>
                <n-avatar
                  v-if="project.project_members.length > 5"
                  round
                  size="small"
                  style="background-color: #e2e8f0"
                >
                  +{{ project.project_members.length - 5 }}
                </n-avatar>
              </n-avatar-group>
              <n-button text size="tiny" type="primary" @click.stop="openEdit(project)">编辑</n-button>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-empty v-else description="暂无项目，点击右上角新建项目" style="padding: 80px 0" />

    <n-drawer v-model:show="showCreateDrawer" :width="520" placement="right">
      <n-drawer-content title="新建项目" :closable="true">
        <n-form ref="createFormRef" :model="createForm" label-placement="top">
          <n-form-item label="项目名称" path="name" :rule="{ required: true, message: '请输入项目名称' }">
            <n-input v-model:value="createForm.name" placeholder="请输入项目名称" />
          </n-form-item>
          <n-form-item label="项目描述">
            <n-input v-model:value="createForm.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
          </n-form-item>
          <n-form-item label="封面颜色">
            <div class="color-picker">
              <div
                v-for="color in coverColors"
                :key="color"
                class="color-option"
                :class="{ active: createForm.cover_color === color }"
                :style="{ backgroundColor: color }"
                @click="createForm.cover_color = color"
              />
            </div>
          </n-form-item>
          <n-form-item label="项目成员">
            <n-checkbox-group v-model:value="createForm.member_ids">
              <n-space vertical>
                <n-checkbox
                  v-for="member in teamMembers"
                  :key="member.user.id"
                  :value="member.user.id"
                >
                  <div class="member-option">
                    <n-avatar round size="small" style="background-color: #2563eb">
                      {{ member.user.name.charAt(0) }}
                    </n-avatar>
                    <span>{{ member.user.name }}</span>
                    <span class="member-email">{{ member.user.email }}</span>
                  </div>
                </n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateDrawer = false">取消</n-button>
            <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <n-drawer v-model:show="showEditDrawer" :width="520" placement="right">
      <n-drawer-content title="编辑项目" :closable="true">
        <n-form ref="editFormRef" :model="editForm" label-placement="top">
          <n-form-item label="项目名称" path="name" :rule="{ required: true, message: '请输入项目名称' }">
            <n-input v-model:value="editForm.name" placeholder="请输入项目名称" />
          </n-form-item>
          <n-form-item label="项目描述">
            <n-input v-model:value="editForm.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
          </n-form-item>
          <n-form-item label="封面颜色">
            <div class="color-picker">
              <div
                v-for="color in coverColors"
                :key="color"
                class="color-option"
                :class="{ active: editForm.cover_color === color }"
                :style="{ backgroundColor: color }"
                @click="editForm.cover_color = color"
              />
            </div>
          </n-form-item>
          <n-form-item label="项目成员">
            <n-checkbox-group v-model:value="editForm.member_ids">
              <n-space vertical>
                <n-checkbox
                  v-for="member in teamMembers"
                  :key="member.user.id"
                  :value="member.user.id"
                >
                  <div class="member-option">
                    <n-avatar round size="small" style="background-color: #2563eb">
                      {{ member.user.name.charAt(0) }}
                    </n-avatar>
                    <span>{{ member.user.name }}</span>
                    <span class="member-email">{{ member.user.email }}</span>
                  </div>
                </n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button type="error" ghost :loading="deleting" @click="handleDelete">删除项目</n-button>
            <n-button @click="showEditDrawer = false">取消</n-button>
            <n-button type="primary" :loading="updating" @click="handleUpdate">保存</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import { listProjectsApi, createProjectApi, updateProjectApi, deleteProjectApi } from '../../api/project'
import { getTeamMembersApi } from '../../api/auth'
import { AddOutline } from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const router = useRouter()
const userStore = useUserStore()
const { message, handleError, dialog } = useApi()

const projects = ref([])
const teamMembers = ref([])
const showCreateDrawer = ref(false)
const showEditDrawer = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const creating = ref(false)
const updating = ref(false)
const deleting = ref(false)
const editingProject = ref(null)

const coverColors = [
  '#2563eb', '#16a34a', '#dc2626', '#9333ea',
  '#ea580c', '#0891b2', '#4f46e5', '#ca8a04',
]

const avatarColors = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2']

const createForm = reactive({
  name: '',
  description: '',
  cover_color: '#2563eb',
  member_ids: [],
})

const editForm = reactive({
  id: null,
  name: '',
  description: '',
  cover_color: '#2563eb',
  member_ids: [],
})

const fetchProjects = async () => {
  try {
    const res = await listProjectsApi()
    projects.value = res
  } catch (e) {
    handleError(e, '获取项目列表失败')
  }
}

const fetchTeamMembers = async () => {
  try {
    const teamId = userStore.currentTeam?.id
    if (teamId) {
      const res = await getTeamMembersApi(teamId)
      teamMembers.value = res
    }
  } catch (e) {
    console.error(e)
  }
}

const goToProject = (projectId) => {
  router.push(`/project/kanban/${projectId}`)
}

const resetCreateForm = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.cover_color = '#2563eb'
  createForm.member_ids = [userStore.user?.id]
}

const handleCreate = async () => {
  try {
    await createFormRef.value?.validate()
  } catch (e) {
    return
  }
  creating.value = true
  try {
    await createProjectApi(createForm)
    message.success('创建成功')
    showCreateDrawer.value = false
    resetCreateForm()
    await fetchProjects()
  } catch (e) {
    handleError(e, '创建失败')
  } finally {
    creating.value = false
  }
}

const openEdit = (project) => {
  editingProject.value = project
  editForm.id = project.id
  editForm.name = project.name
  editForm.description = project.description
  editForm.cover_color = project.cover_color
  editForm.member_ids = project.project_members.map((m) => m.user.id)
  showEditDrawer.value = true
}

const handleUpdate = async () => {
  try {
    await editFormRef.value?.validate()
  } catch (e) {
    return
  }
  updating.value = true
  try {
    await updateProjectApi(editForm.id, editForm)
    message.success('保存成功')
    showEditDrawer.value = false
    await fetchProjects()
  } catch (e) {
    handleError(e, '保存失败')
  } finally {
    updating.value = false
  }
}

const handleDelete = () => {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除该项目吗？删除后无法恢复。',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      deleting.value = true
      try {
        await deleteProjectApi(editForm.id)
        message.success('删除成功')
        showEditDrawer.value = false
        await fetchProjects()
      } catch (e) {
        handleError(e, '删除失败')
      } finally {
        deleting.value = false
      }
    },
  })
}

onMounted(async () => {
  resetCreateForm()
  await fetchTeamMembers()
  await fetchProjects()
})
</script>

<style lang="scss" scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #1f2937;
  }
}

.project-card {
  cursor: pointer;
  padding: 0 !important;
  overflow: hidden;

  :deep(.n-card__content) {
    padding: 0;
  }
}

.project-cover {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;

  .project-initials {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 2px;
  }
}

.project-info {
  padding: 16px;

  .project-name {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 8px;
  }

  .project-desc {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 12px;
    min-height: 36px;

    &.empty {
      color: #94a3b8;
    }
  }

  .project-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  .color-option {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;

    &.active {
      border-color: #1f2937;
      transform: scale(1.1);
    }
  }
}

.member-option {
  display: flex;
  align-items: center;
  gap: 10px;

  .member-email {
    font-size: 12px;
    color: #94a3b8;
    margin-left: 6px;
  }
}
</style>
