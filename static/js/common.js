function parseCompletionChartSegments(value) {
  return value
    .split(',')
    .map(function (segment) {
      const parts = segment.split('|');
      return {
        percent: Number(parts[0]),
        color: parts[1],
      };
    })
    .filter(function (segment) {
      return segment.percent > 0 && segment.color;
    });
}

function buildCompletionChartGradient(segments, progress) {
  let cursor = 0;
  const stops = [];

  segments.forEach(function (segment) {
    const size = segment.percent * progress;
    const next = cursor + size;
    stops.push(segment.color + ' ' + cursor + '% ' + next + '%');
    cursor = next;
  });

  if (cursor < 100) {
    stops.push('#E1E4EB ' + cursor + '% 100%');
  }

  return 'conic-gradient(' + stops.join(', ') + ')';
}

function animateCompletionChart(chart, animationDuration) {
  const segments = parseCompletionChartSegments(chart.dataset.chartSegments || '');
  const targetPercent = Number(chart.dataset.completedPercent || 0);
  const valueLabel = chart.querySelector('[data-completion-value]');
  const startedAt = performance.now();

  function animateChart(now) {
    const progress = Math.min((now - startedAt) / animationDuration, 1);
    chart.style.background = buildCompletionChartGradient(segments, progress);

    if (valueLabel) {
      valueLabel.textContent = Math.round(targetPercent * progress) + '%';
    }

    if (progress < 1) {
      requestAnimationFrame(animateChart);
    }
  }

  requestAnimationFrame(animateChart);
}

function initCompletionCharts() {
  const animationDuration = 900;

  document.querySelectorAll('[data-completion-chart]').forEach(function (chart) {
    animateCompletionChart(chart, animationDuration);
  });
}

function initMetricGroups() {
  requestAnimationFrame(function () {
    document.querySelectorAll('.metric-fill').forEach(function (fill) {
      fill.style.width = fill.dataset.targetPercent + '%';
    });
  });
}

function initCommonComponents() {
  initCompletionCharts();
  initMetricGroups();
}

document.addEventListener('DOMContentLoaded', initCommonComponents);
