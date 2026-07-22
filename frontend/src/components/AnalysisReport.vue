<template>
  <div class="report">
    <button class="back-btn" @click="$emit('back')">← 返回上传</button>

    <!-- Overall score -->
    <div class="overall-card">
      <div class="score-ring" :class="scoreLevel">
        <span class="score-num">{{ report.overall_score }}</span>
      </div>
      <div class="overall-info">
        <h2>整体评分</h2>
        <p class="stat">动作片段: {{ report.statistics.total_segments }} 个</p>
        <div class="type-badges">
          <span v-for="(cnt, type) in report.statistics.by_type" :key="type" class="badge">
            {{ typeLabel(type) }} ×{{ cnt }}
          </span>
        </div>
      </div>
    </div>

    <!-- Per-segment detail -->
    <div v-for="(seg, idx) in report.action_segments" :key="idx" class="segment-card">
      <div class="seg-header">
        <span class="seg-type">{{ typeLabel(seg.action_type) }}</span>
        <span class="seg-time">{{ seg.start_ms }}ms - {{ seg.end_ms }}ms</span>
        <span class="sim-score" :class="scoreLevelFor(seg.similarity_score)">
          {{ seg.similarity_score }} 分
        </span>
      </div>
      <p class="template-src">对比模板: {{ templateLabel(seg.template_source) }}</p>

      <ComparisonPlayer
        v-if="seg.user_video_url && seg.template_video_url"
        :userUrl="seg.user_video_url"
        :tmplUrl="seg.template_video_url"
      />

      <table class="metrics-table">
        <thead>
          <tr>
            <th>指标</th>
            <th>你的数值</th>
            <th>模板数值</th>
            <th>偏差</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in seg.metrics" :key="m.name" :class="m.level">
            <td>{{ metricLabel(m.name) }}</td>
            <td>{{ fmtNum(m.user_value) }}</td>
            <td>{{ fmtNum(m.template_value) }}</td>
            <td>{{ fmtNum(m.diff) }}</td>
            <td>
              <span class="level-tag" :class="m.level">
                {{ levelLabel(m.level) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-for="m in seg.metrics" :key="m.name + '-fb'" class="feedback">
        <p v-if="m.problem" class="problem">⚠️ {{ m.problem }}</p>
        <p v-if="m.suggestion" class="suggestion">💡 {{ m.suggestion }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ComparisonPlayer from './ComparisonPlayer.vue'

const props = defineProps({ report: Object })
defineEmits(['back'])

const scoreLevel = computed(() => {
  const s = props.report.overall_score
  return s >= 80 ? 'good' : s >= 60 ? 'fair' : 'poor'
})

function scoreLevelFor(s) {
  return s >= 80 ? 'good' : s >= 60 ? 'fair' : 'poor'
}

function typeLabel(t) {
  const map = {
    fore_topspin: '正手拉上旋',
    back_topspin: '反手拉上旋',
    fore_underspin: '正手起下旋',
    back_underspin: '反手起下旋',
  }
  return map[t] || t
}

function templateLabel(t) {
  return { ma_long: '马龙', fan_zhendong: '樊振东' }[t] || t
}

function metricLabel(m) {
  const map = {
    elbow_angle: '肘关节夹角',
    racket_height: '引拍高度',
    hip_rotation: '转腰髋偏移',
    cog_fluctuation: '重心起伏',
    swing_range: '挥拍轨迹范围',
    swing_speed: '挥拍加速度',
  }
  return map[m] || m
}

function levelLabel(l) {
  return { good: '良好', fair: '需改善', poor: '待加强' }[l] || l
}

function fmtNum(v) {
  if (v == null || isNaN(v)) return '-'
  return Math.abs(v) < 0.01 ? v.toFixed(4) : v.toFixed(2)
}
</script>

<style scoped>
.report { max-width: 780px; margin: 0 auto; }
.back-btn {
  margin-bottom: 16px; padding: 8px 16px; border: none; border-radius: 6px;
  background: #e8ecf0; color: #333; cursor: pointer; font-size: 13px;
}
.back-btn:hover { background: #d5d9e0; }

.overall-card {
  background: #fff; border-radius: 12px; padding: 24px;
  display: flex; align-items: center; gap: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px;
}
.score-ring {
  width: 96px; height: 96px; border-radius: 50%; border: 6px solid #e8ecf0;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.score-ring.good { border-color: #2ecc71; }
.score-ring.fair { border-color: #f39c12; }
.score-ring.poor { border-color: #e74c3c; }
.score-num { font-size: 28px; font-weight: 700; }
.overall-info h2 { font-size: 18px; margin-bottom: 4px; }
.stat { color: #666; font-size: 14px; margin-bottom: 8px; }
.type-badges { display: flex; flex-wrap: wrap; gap: 6px; }
.badge {
  background: #eef2ff; color: #4f6ef7; padding: 2px 10px; border-radius: 12px;
  font-size: 12px;
}

.segment-card {
  background: #fff; border-radius: 12px; padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px;
}
.seg-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 8px;
  flex-wrap: wrap;
}
.seg-type { font-weight: 600; font-size: 16px; }
.seg-time { color: #999; font-size: 12px; }
.sim-score {
  margin-left: auto; font-weight: 700; font-size: 18px;
}
.sim-score.good { color: #2ecc71; }
.sim-score.fair { color: #f39c12; }
.sim-score.poor { color: #e74c3c; }
.template-src { color: #999; font-size: 12px; margin-bottom: 12px; }

.metrics-table {
  width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 12px;
}
.metrics-table th {
  text-align: left; padding: 6px 8px; border-bottom: 1px solid #eee;
  color: #666; font-weight: 500;
}
.metrics-table td { padding: 8px; border-bottom: 1px solid #f5f5f5; }
.metrics-table tr.poor td { background: #fff5f5; }
.metrics-table tr.fair td { background: #fffbf0; }
.level-tag {
  display: inline-block; padding: 1px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 500;
}
.level-tag.good { background: #e8f8f0; color: #27ae60; }
.level-tag.fair { background: #fef3e2; color: #e67e22; }
.level-tag.poor { background: #fde8e8; color: #e74c3c; }

.feedback { margin-top: 8px; }
.feedback p { font-size: 13px; margin-bottom: 4px; padding: 6px 10px; border-radius: 6px; }
.problem { background: #fff5f5; color: #c0392b; }
.suggestion { background: #f0f9ff; color: #2980b9; }
</style>
