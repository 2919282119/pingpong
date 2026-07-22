<template>
  <div class="tab-bar">
    <div
      v-for="tab in tabs" :key="tab.path"
      class="tab-item" :class="{ active: tab.active }"
      @click="tab.onClick"
    >
      <span class="tab-icon" v-html="tab.icon"></span>
      <span class="tab-label">{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tabs: { type: Array, required: true },
})
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(var(--tab-bar-height) + var(--safe-area-bottom));
  padding-bottom: var(--safe-area-bottom);
  background: #fff;
  border-top: 1px solid #eee;
  display: flex;
  z-index: 1000;
}
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
.tab-item.active {
  color: #1485ee;
}
.tab-icon {
  font-size: 22px;
  line-height: 1;
  margin-bottom: 2px;
}
.tab-icon :deep(svg) {
  width: 22px;
  height: 22px;
  fill: currentColor;
}
.tab-label {
  font-size: 11px;
  line-height: 1;
}
</style>
