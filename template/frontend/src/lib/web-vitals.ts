import { onCLS, onINP, onFCP, onLCP, onTTFB, type Metric } from 'web-vitals'

function logMetric(metric: Metric) {
  if (import.meta.env.DEV) {
    console.log('[Web Vitals]', metric.name, metric.value, metric)
  }
}

/** Initialize Web Vitals tracking. Call once when the app starts. */
export function initWebVitals() {
  onCLS(logMetric)
  onINP(logMetric)
  onFCP(logMetric)
  onLCP(logMetric)
  onTTFB(logMetric)
}
