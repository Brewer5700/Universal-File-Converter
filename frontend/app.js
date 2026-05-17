const state = {
  formats: [],
  supportedTargets: {},
  selectedFiles: [],
  polling: null,
};

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const formatSearch = document.getElementById('formatSearch');
const formatList = document.getElementById('formatList');
const targetFormat = document.getElementById('targetFormat');
const supportedInfo = document.getElementById('supportedInfo');
const statusEl = document.getElementById('status');
const progressBar = document.getElementById('progressBar');
const resultsEl = document.getElementById('results');
const convertButton = document.getElementById('convertButton');
const apiKeyInput = document.getElementById('apiKey');

const API_KEY_STORAGE = 'ufc_api_key';

function getApiKey() {
  return apiKeyInput.value.trim();
}

function apiHeaders() {
  const headers = {};
  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return headers;
}

function saveApiKey() {
  localStorage.setItem(API_KEY_STORAGE, getApiKey());
}

function loadApiKey() {
  const saved = localStorage.getItem(API_KEY_STORAGE);
  if (saved) {
    apiKeyInput.value = saved;
  }
}

async function fetchFormats() {
  const response = await fetch('/api/formats', { headers: apiHeaders() });
  if (!response.ok) {
    throw new Error('Unable to load formats.');
  }
  const data = await response.json();
  state.formats = data.formats || [];
  state.supportedTargets = data.supported_targets || {};
  renderFormats();
}

function renderFormats() {
  const search = formatSearch.value.trim().toLowerCase();
  formatList.innerHTML = '';

  state.formats.forEach(category => {
    const filtered = category.formats.filter(item =>
      item.ext.toLowerCase().includes(search) || item.label.toLowerCase().includes(search)
    );
    if (!filtered.length) {
      return;
    }
    const section = document.createElement('div');
    section.className = 'format-category';

    const title = document.createElement('h3');
    title.textContent = category.category;
    section.appendChild(title);

    const pills = document.createElement('div');
    pills.className = 'format-pills';

    filtered.forEach(item => {
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'pill';
      pill.textContent = item.label;
      pill.dataset.format = item.ext;
      pill.addEventListener('click', () => {
        targetFormat.value = item.ext;
      });
      pills.appendChild(pill);
    });

    section.appendChild(pills);
    formatList.appendChild(section);
  });
}

function renderFiles() {
  fileList.innerHTML = '';
  state.selectedFiles.forEach(file => {
    const li = document.createElement('li');
    li.textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
    fileList.appendChild(li);
  });
  updateSupportedInfo();
}

async function updateSupportedInfo() {
  if (!state.selectedFiles.length) {
    supportedInfo.textContent = '';
    return;
  }
  const firstFile = state.selectedFiles[0];
  const ext = firstFile.name.split('.').pop().toLowerCase();
  try {
    const response = await fetch(`/api/conversions?input_ext=${encodeURIComponent(ext)}`, {
      headers: apiHeaders(),
    });
    if (!response.ok) {
      supportedInfo.textContent = 'No conversions available for selected file type.';
      return;
    }
    const data = await response.json();
    supportedInfo.textContent = `Supported outputs for .${data.input}: ${data.targets.join(', ')}`;
  } catch (error) {
    supportedInfo.textContent = 'Unable to load supported conversions.';
  }
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = `status ${isError ? 'error' : ''}`;
}

function setProgress(value) {
  progressBar.style.width = `${value}%`;
}

async function startConversion() {
  if (!state.selectedFiles.length) {
    setStatus('Select at least one file.', true);
    return;
  }
  const target = targetFormat.value.trim();
  if (!target) {
    setStatus('Enter a target format.', true);
    return;
  }

  saveApiKey();

  const formData = new FormData();
  formData.append('target_format', target);
  state.selectedFiles.forEach(file => formData.append('files', file));

  setStatus('Creating job...');
  setProgress(0);
  resultsEl.innerHTML = '';

  try {
    const response = await fetch('/api/jobs', {
      method: 'POST',
      body: formData,
      headers: apiHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Unable to create job.');
    }
    pollJob(data.job.job_id);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function pollJob(jobId) {
  if (state.polling) {
    clearInterval(state.polling);
  }

  state.polling = setInterval(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`, { headers: apiHeaders() });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to fetch job.');
      }
      const job = data.job;
      setProgress(job.progress);
      setStatus(`Status: ${job.status}`);

      if (job.status === 'failed') {
        clearInterval(state.polling);
        setStatus(job.error || 'Conversion failed.', true);
      }
      if (job.status === 'completed') {
        clearInterval(state.polling);
        renderResults(job.outputs);
      }
    } catch (error) {
      clearInterval(state.polling);
      setStatus(error.message, true);
    }
  }, 1000);
}

function renderResults(outputs) {
  if (!outputs || !outputs.length) {
    resultsEl.textContent = 'No outputs available.';
    return;
  }
  resultsEl.innerHTML = '<h3>Results</h3>';
  const list = document.createElement('ul');
  outputs.forEach(output => {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = output.download_url;
    link.textContent = output.filename;
    link.target = '_blank';
    item.appendChild(link);
    list.appendChild(item);
  });
  resultsEl.appendChild(list);
}

function bindEvents() {
  dropZone.addEventListener('dragover', event => {
    event.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', event => {
    event.preventDefault();
    dropZone.classList.remove('dragover');
    const files = Array.from(event.dataTransfer.files || []);
    if (files.length) {
      state.selectedFiles = files;
      renderFiles();
    }
  });

  fileInput.addEventListener('change', event => {
    const files = Array.from(event.target.files || []);
    state.selectedFiles = files;
    renderFiles();
  });

  formatSearch.addEventListener('input', renderFormats);
  convertButton.addEventListener('click', startConversion);
  apiKeyInput.addEventListener('change', saveApiKey);
}

loadApiKey();
bindEvents();
fetchFormats().catch(error => setStatus(error.message, true));
