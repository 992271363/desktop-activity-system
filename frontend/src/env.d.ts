// frontend/src/env.d.ts

/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // 使用 object 替代 {}，使用 unknown 替代 any
  const component: DefineComponent<object, object, unknown>
  export default component
}
