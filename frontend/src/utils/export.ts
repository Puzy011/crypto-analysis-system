/**
 * 数据导出工具
 */

/**
 * 导出为 JSON 文件
 */
export function exportToJSON(data: any, filename: string = 'data.json') {
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  downloadBlob(blob, filename)
}

/**
 * 导出为 CSV 文件
 */
export function exportToCSV(data: any[], filename: string = 'data.csv') {
  if (!data || data.length === 0) {
    console.warn('No data to export')
    return
  }

  // 获取表头
  const headers = Object.keys(data[0])
  
  // 构建 CSV 内容
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header]
        // 处理包含逗号或换行的值
        if (typeof value === 'string' && (value.includes(',') || value.includes('\n'))) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value
      }).join(',')
    )
  ].join('\n')

  // 添加 BOM 以支持中文
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, filename)
}

/**
 * 导出为 Excel 文件（简单版，使用 CSV 格式）
 */
export function exportToExcel(data: any[], filename: string = 'data.xlsx') {
  // 简单实现：使用 CSV 格式，但文件名为 .xlsx
  // 如需完整 Excel 支持，建议使用 xlsx 库
  exportToCSV(data, filename.replace('.xlsx', '.csv'))
}

/**
 * 下载 Blob 对象
 */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  // 释放 URL 对象
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

/**
 * 复制文本到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      const successful = document.execCommand('copy')
      document.body.removeChild(textArea)
      return successful
    }
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}

/**
 * 打印页面
 */
export function printPage() {
  window.print()
}

/**
 * 生成时间戳文件名
 */
export function generateFilename(prefix: string = 'export', extension: string = 'json'): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  return `${prefix}_${timestamp}.${extension}`
}
