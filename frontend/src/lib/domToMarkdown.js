function inlineToMarkdown(el) {
  let out = ''
  el.childNodes.forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      out += node.textContent
      return
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return

    const tag = node.tagName.toLowerCase()
    if (tag === 'code') out += `\`${node.textContent}\``
    else if (tag === 'strong' || tag === 'b') out += `**${inlineToMarkdown(node)}**`
    else if (tag === 'em' || tag === 'i') out += `_${inlineToMarkdown(node)}_`
    else if (tag === 'a') out += `[${inlineToMarkdown(node)}](${node.getAttribute('href')})`
    else out += inlineToMarkdown(node)
  })
  return out
}

function elementToMarkdown(el) {
  return Array.from(el.childNodes)
    .map(nodeToMarkdown)
    .filter(Boolean)
    .join('\n\n')
}

function nodeToMarkdown(node) {
  if (node.nodeType === Node.TEXT_NODE) return node.textContent.trim()
  if (node.nodeType !== Node.ELEMENT_NODE) return ''

  if (node.hasAttribute('data-codeblock')) {
    const titleEl = node.querySelector('[data-codeblock-title]')
    const codeEl = node.querySelector('pre code')
    const title = titleEl ? titleEl.textContent.trim() : ''
    const code = codeEl ? codeEl.textContent : ''
    return (title ? `**${title}**\n\n` : '') + '```\n' + code + '\n```'
  }

  const tag = node.tagName.toLowerCase()
  switch (tag) {
    case 'h1':
      return `# ${inlineToMarkdown(node)}`
    case 'h2':
      return `## ${inlineToMarkdown(node)}`
    case 'h3':
      return `### ${inlineToMarkdown(node)}`
    case 'p':
      return inlineToMarkdown(node)
    case 'ul':
      return Array.from(node.children)
        .map((li) => `- ${inlineToMarkdown(li)}`)
        .join('\n')
    case 'pre': {
      const codeEl = node.querySelector('code')
      return '```\n' + (codeEl ? codeEl.textContent : node.textContent) + '\n```'
    }
    case 'table': {
      const headRow = node.querySelector('thead tr')
      const headers = headRow
        ? Array.from(headRow.children).map((th) => th.textContent.trim())
        : []
      const rows = Array.from(node.querySelectorAll('tbody tr')).map((tr) =>
        Array.from(tr.children).map((td) => td.textContent.trim()),
      )
      const headerLine = `| ${headers.join(' | ')} |`
      const sepLine = `| ${headers.map(() => '---').join(' | ')} |`
      const bodyLines = rows.map((r) => `| ${r.join(' | ')} |`)
      return [headerLine, sepLine, ...bodyLines].join('\n')
    }
    default:
      return elementToMarkdown(node)
  }
}

export function articleToMarkdown(el) {
  if (!el) return ''
  return elementToMarkdown(el).replace(/\n{3,}/g, '\n\n').trim()
}
