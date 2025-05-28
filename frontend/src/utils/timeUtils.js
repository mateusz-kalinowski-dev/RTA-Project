export function getTimeRange(range) {
  const to = new Date()
  const from = new Date(to)
  if (range === '1h') from.setHours(to.getHours() - 1)
  else if (range === '3h') from.setHours(to.getHours() - 3)
  else from.setDate(to.getDate() - 1)

  return {
    from: from.toISOString(),
    to: to.toISOString(),
  }
}