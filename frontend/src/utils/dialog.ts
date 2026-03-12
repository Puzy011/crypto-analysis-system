/**
 * 对话框工具函数
 */
import { ElMessageBox, ElMessage, ElNotification } from 'element-plus'

/**
 * 确认对话框
 */
export function confirmDialog(
  message: string,
  title: string = '确认',
  options: any = {}
): Promise<any> {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    ...options
  })
}

/**
 * 删除确认对话框
 */
export function confirmDelete(
  message: string = '此操作将永久删除该数据，是否继续？',
  title: string = '删除确认'
): Promise<any> {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'error',
    confirmButtonClass: 'el-button--danger'
  })
}

/**
 * 提示对话框
 */
export function alertDialog(
  message: string,
  title: string = '提示',
  type: 'success' | 'warning' | 'info' | 'error' = 'info'
): Promise<any> {
  return ElMessageBox.alert(message, title, {
    confirmButtonText: '确定',
    type
  })
}

/**
 * 输入对话框
 */
export function promptDialog(
  message: string,
  title: string = '请输入',
  options: any = {}
): Promise<{ value: string }> {
  return ElMessageBox.prompt(message, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    ...options
  })
}

/**
 * 成功消息
 */
export function successMessage(message: string, duration: number = 3000) {
  ElMessage.success({
    message,
    duration,
    showClose: true
  })
}

/**
 * 错误消息
 */
export function errorMessage(message: string, duration: number = 3000) {
  ElMessage.error({
    message,
    duration,
    showClose: true
  })
}

/**
 * 警告消息
 */
export function warningMessage(message: string, duration: number = 3000) {
  ElMessage.warning({
    message,
    duration,
    showClose: true
  })
}

/**
 * 信息消息
 */
export function infoMessage(message: string, duration: number = 3000) {
  ElMessage.info({
    message,
    duration,
    showClose: true
  })
}

/**
 * 成功通知
 */
export function successNotification(
  title: string,
  message: string = '',
  duration: number = 4500
) {
  ElNotification.success({
    title,
    message,
    duration
  })
}

/**
 * 错误通知
 */
export function errorNotification(
  title: string,
  message: string = '',
  duration: number = 4500
) {
  ElNotification.error({
    title,
    message,
    duration
  })
}

/**
 * 警告通知
 */
export function warningNotification(
  title: string,
  message: string = '',
  duration: number = 4500
) {
  ElNotification.warning({
    title,
    message,
    duration
  })
}

/**
 * 信息通知
 */
export function infoNotification(
  title: string,
  message: string = '',
  duration: number = 4500
) {
  ElNotification.info({
    title,
    message,
    duration
  })
}
