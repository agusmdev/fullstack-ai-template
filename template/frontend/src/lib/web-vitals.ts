/**
 * Web Vitals tracking
 * Tracks Core Web Vitals metrics for performance monitoring
 */

import { onCLS, onINP, onFCP, onLCP, onTTFB, type Metric } from 'web-vitals'

/**
 * Log metric to console in development
 * In production, you would send this to an analytics service
 */
function logMetric(metric: Metric) {
  // In development, log to console
  if (import.meta.env.DEV) {
    console.log('[Web Vitals]', metric.name, metric.value, metric)
  }

  // In production, send to analytics service
  // Example: sendToAnalytics(metric)
}

/**
 * Initialize Web Vitals tracking
 * Call this once when the app starts
 *
 * Tracks the following metrics:
 * - CLS (Cumulative Layout Shift)
 * - INP (Interaction to Next Paint) - replaces FID
 * - FCP (First Contentful Paint)
 * - LCP (Largest Contentful Paint)
 * - TTFB (Time to First Byte)
 */
export function initWebVitals() {
  onCLS(logMetric)
  onINP(logMetric)
  onFCP(logMetric)
  onLCP(logMetric)
  onTTFB(logMetric)
}
