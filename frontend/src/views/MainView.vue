<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>我的仪表盘</h1>
      <p>你好，{{ username }}！这里是你应用使用情况的实时概览。</p>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <h3>今日焦点时长</h3>
        <p>{{ formatDuration(stats.todayFocusSeconds) }}</p>
        <span class="card-icon"><i class="fas fa-clock"></i></span>
      </div>
      <div class="stat-card">
        <h3>总计追踪应用</h3>
        <p>{{ stats.totalAppsTracked }} 个</p>
        <span class="card-icon"><i class="fas fa-rocket"></i></span>
      </div>
      <div class="stat-card">
        <h3>今日最常用应用</h3>
        <p>{{ stats.mostUsedAppToday || '加载中...' }}</p>
        <span class="card-icon"><i class="fas fa-crown"></i></span>
      </div>
      <div class="stat-card">
        <h3>本周总运行时长</h3>
        <p>{{ formatDuration(stats.thisWeekLifetimeSeconds) }}</p>
        <span class="card-icon"><i class="fas fa-calendar-week"></i></span>
      </div>
    </div>

    <div class="dashboard-body">
      <main class="main-content">
        <h2>应用使用总览</h2>
        <div class="app-list">
          <div v-for="app in topApps" :key="app.id" class="app-item">
            <div class="app-info">
              <span class="app-name">{{ formatAppName(app.executable_name) }}</span>
              <span class="app-last-seen"
                >最后使用: {{ new Date(app.summary.last_seen_end_at).toLocaleString() }}</span
              >
            </div>
            <div class="app-stats">
              <div class="stat-focus">
                <strong>专注时长:</strong>
                {{ formatDuration(app.summary.total_focus_time_seconds) }}
              </div>
              <div class="stat-lifetime">
                <strong>总运行时长:</strong>
                {{ formatDuration(app.summary.total_lifetime_seconds) }}
              </div>
            </div>
            <div class="focus-progress">
              <div
                class="progress-bar"
                :style="{
                  width:
                    (app.summary.total_focus_time_seconds / app.summary.total_lifetime_seconds) *
                      100 +
                    '%',
                }"
              ></div>
            </div>
          </div>
          <div v-if="topApps.length === 0" class="empty-state">
            <p>正在加载数据或暂无应用数据...</p>
          </div>
        </div>
      </main>

      <aside class="sidebar">
        <h2>最近活动会话</h2>
        <ul class="activity-feed">
          <li v-for="activity in recentActivities" :key="activity.id" class="feed-item">
            <div class="feed-icon"><i class="fas fa-history"></i></div>
            <div class="feed-content">
              <strong>{{ activity.process_name }}</strong>
              <small>持续了 {{ formatDuration(activity.total_lifetime_seconds) }}</small>
              <small
                >{{ new Date(activity.session_start_time).toLocaleTimeString() }} -
                {{ new Date(activity.session_end_time).toLocaleTimeString() }}</small
              >
            </div>
          </li>
          <li v-if="recentActivities.length === 0" class="empty-state">
            <p>正在加载或暂无最近活动...</p>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const formatAppName = (name: string): string => {
  return name.replace(/\.exe$/i, '')
} 

interface DashboardStats {
  todayFocusSeconds: number
  totalAppsTracked: number
  mostUsedAppToday: string | null
  thisWeekLifetimeSeconds: number
}

interface AppSummary {
  last_seen_end_at: string
  total_lifetime_seconds: number
  total_focus_time_seconds: number
}

interface WatchedApplication {
  id: number
  executable_name: string
  summary: AppSummary
}

interface ProcessSession {
  id: number
  process_name: string
  session_start_time: string
  session_end_time: string
  total_lifetime_seconds: number
}

const username = ref(authStore.username || 'User')

const stats = ref<DashboardStats>({
  todayFocusSeconds: 0,
  totalAppsTracked: 0,
  mostUsedAppToday: null,
  thisWeekLifetimeSeconds: 0,
})

const topApps = ref<WatchedApplication[]>([])
const recentActivities = ref<ProcessSession[]>([])

const formatDuration = (totalSeconds: number): string => {
  if (totalSeconds < 60) {
    return `${Math.round(totalSeconds)}秒`
  }
  const days = Math.floor(totalSeconds / (24 * 3600))
  const hours = Math.floor((totalSeconds % (24 * 3600)) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  let result = ''
  if (days > 0) {
    result += `${days}天 `
    if (hours > 0) result += `${hours}小时 `
    return result.trim()
  }

  if (hours > 0) result += `${hours}小时 `
  if (minutes > 0) result += `${minutes}分钟`
  
  return result.trim() || '0分钟'
}

const fetchData = async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  try {
    const [statsRes, appsRes, activityRes] = await Promise.all([
      request.get('/dashboard/stats'),
      request.get('/dashboard/apps?sort_by=focus_time'),
      request.get('/dashboard/recent-activity?limit=10'),
    ])


    stats.value = statsRes as unknown as DashboardStats
    topApps.value = appsRes as unknown as WatchedApplication[]
    recentActivities.value = activityRes as unknown as ProcessSession[]
  } catch (error) {
    console.error('无法加载仪表盘数据:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  color: #e2e8f0;
}

.dashboard-header {
  margin-bottom: 2rem;
}
.dashboard-header h1 {
  font-size: 2.25rem;
  font-weight: 700;
  color: #f7fafc;
  margin: 0;
}
.dashboard-header p {
  color: #a0aec0;
  font-size: 1.1rem;
  margin-top: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.dashboard-body {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 1.5rem;
  align-items: flex-start;
}

.stat-card,
.main-content,
.sidebar {
  background: rgba(30, 35, 50, 0.55);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  border-color: rgba(66, 153, 225, 0.6);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.main-content h2,
.sidebar h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-top: 0;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  color: #a0aec0;
  font-weight: 500;
}
.stat-card p {
  margin: 0;
  font-size: 2.25rem;
  font-weight: 700;
  color: #f7fafc;
}
.stat-card .card-icon {
  position: absolute;
  right: 1.5rem;
  top: 1.5rem;
  font-size: 1.75rem;
  color: rgba(255, 255, 255, 0.15);
}

.app-list,
.activity-feed {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  list-style: none;
  padding: 0;
}

.app-item,
.feed-item {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 1rem;
}

.app-item:last-child,
.feed-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.app-item {
  display: flex;
  flex-direction: column;
}
.app-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.app-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #f7fafc;
}
.app-last-seen {
  font-size: 0.8rem;
  color: #718096;
}
.app-stats {
  display: flex;
  gap: 2rem;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  color: #a0aec0;
}
.app-stats strong {
  color: #cbd5e0;
}

.focus-progress {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
  height: 8px;
  overflow: hidden;
  margin-top: auto;
}
.progress-bar {
  background-color: #4299e1;
  height: 100%;
  border-radius: 99px;
}

.feed-item {
  position: relative;
  padding-left: 2rem;
}
.feed-icon {
  position: absolute;
  top: 0;
  left: 0;
  color: #718096;
}
.feed-content {
  display: flex;
  flex-direction: column;
}
.feed-content strong {
  color: #e2e8f0;
}
.feed-content small {
  color: #a0aec0;
  font-size: 0.8rem;
}

.empty-state {
  background: transparent;
  padding: 2rem 1rem;
  text-align: center;
  color: #a0aec0;
  border: none;
}
</style>
