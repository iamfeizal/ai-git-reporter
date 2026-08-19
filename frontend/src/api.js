/**
 * API Client — Communicates with the FastAPI backend.
 * All requests proxied via Vite dev server to http://localhost:8000
 */

const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  const res = await fetch(url, config);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || `Request failed: ${res.status}`);
  }
  return data;
}

// --- Config: LLM ---
export const fetchLLMs = () => request('/config/llm');
export const createLLM = (config) => request('/config/llm', { method: 'POST', body: JSON.stringify(config) });
export const updateLLM = (id, config) => request(`/config/llm/${id}`, { method: 'PUT', body: JSON.stringify(config) });
export const activateLLM = (id) => request(`/config/llm/${id}/activate`, { method: 'PUT' });
export const deleteLLM = (id) => request(`/config/llm/${id}`, { method: 'DELETE' });
export const testLLM = (config) => request('/config/llm/test', { method: 'POST', body: JSON.stringify({ ...config, is_active: false }) });

// --- Config: GitLab ---
export const fetchGitLabs = () => request('/config/gitlab');
export const createGitLab = (instance) => request('/config/gitlab', { method: 'POST', body: JSON.stringify(instance) });
export const deleteGitLab = (id) => request(`/config/gitlab/${id}`, { method: 'DELETE' });
export const fetchProjects = (instanceId) => request(`/config/gitlab/${instanceId}/projects`);

// --- Test GitLab commits ---
export const testGitLabCommits = (params) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/test-gitlab?${qs}`);
};

// --- Workflow (HITL Pipeline) ---
export const startWorkflow = (payload) => request('/workflow/start', { method: 'POST', body: JSON.stringify(payload) });
export const getWorkflowStatus = (threadId) => request(`/workflow/${threadId}/status`);
export const getWorkflowState = (threadId) => request(`/workflow/${threadId}/state`);
export const resumeWorkflow = (threadId, payload) =>
  request(`/workflow/${threadId}/resume`, { method: 'POST', body: JSON.stringify(payload) });

// --- Legacy full pipeline ---
export const generateReportFull = (payload) =>
  request('/generate-report/full-pipeline', { method: 'POST', body: JSON.stringify(payload) });
