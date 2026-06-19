export function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)
  html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
    return `<pre><code>${code.trim()}</code></pre>`
  })
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>')
  html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>')
  html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>')
  html = html.replace(/^\s*[-*+]\s+\[x\]\s+(.*)$/gim, '<li class="task-done"><input type="checkbox" checked disabled> $1</li>')
  html = html.replace(/^\s*[-*+]\s+\[ \]\s+(.*)$/gim, '<li class="task"><input type="checkbox" disabled> $1</li>')
  html = html.replace(/^\s*[-*+]\s+(.*)$/gm, '<li>$1</li>')
  html = html.replace(/^\s*\d+\.\s+(.*)$/gm, '<li>$1</li>')
  html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%">')
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  html = '<p>' + html + '</p>'
  html = html.replace(/(<\/?h[1-6]>|<\/?pre>|<\/?blockquote>|<\/?ul>|<\/?ol>|<li>.*?<\/li>)/g, (match) => {
    return match.replace(/^<p>|<\/p>$/g, '')
  })
  return html
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

export function buildNodeIdMap(nodes) {
  const map = {}
  const walk = (list) => {
    for (const node of list) {
      map[node.id] = node
      if (node.children && node.children.length > 0) {
        walk(node.children)
      }
    }
  }
  walk(nodes)
  return map
}

export function collectFolderIds(nodes, ids = []) {
  for (const node of nodes) {
    if (node.children && node.children.length > 0) {
      if (!ids.includes(node.id)) ids.push(node.id)
      collectFolderIds(node.children, ids)
    }
  }
  return ids
}

export function findSiblings(nodes, parentId) {
  if (!parentId) return nodes
  for (const node of nodes) {
    if (node.id === parentId) return node.children || []
    if (node.children) {
      const found = findSiblings(node.children, parentId)
      if (found) return found
    }
  }
  return []
}

export function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  return d.toLocaleString('zh-CN')
}
