import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const getAccessToken = () => localStorage.getItem('access_token');
export const getRefreshToken = () => localStorage.getItem('refresh_token');
export const saveTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};
export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

const axiosInstance = axios.create({
  baseURL: BASE_URL,
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/login' && originalRequest.url !== '/auth/refresh') {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return axiosInstance(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        isRefreshing = false;
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
        saveTokens(data.access_token, data.refresh_token);
        axiosInstance.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token;
        originalRequest.headers['Authorization'] = 'Bearer ' + data.access_token;
        processQueue(null, data.access_token);
        return axiosInstance(originalRequest);
      } catch (err) {
        processQueue(err, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Authentication
  async register(email, password, full_name, company_name = '') {
    const response = await axiosInstance.post('/auth/register', { email, password, full_name, company_name });
    return response.data;
  },

  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const response = await axiosInstance.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    const tokens = response.data;
    saveTokens(tokens.access_token, tokens.refresh_token);
    return await this.getMe();
  },

  async logout() {
    try {
      await axiosInstance.post('/auth/logout');
    } finally {
      clearTokens();
    }
  },

  async getMe() {
    const response = await axiosInstance.get('/auth/me');
    return response.data.data;
  },

  // Organizations
  async getOrganizations() {
    const response = await axiosInstance.get('/organizations');
    return response.data.data;
  },

  async createOrganization(name, description) {
    const response = await axiosInstance.post('/organizations', { name, description });
    return response.data.data;
  },

  async getOrgStats(orgId) {
    // Intentionally kept static for hackathon
    return {
      total_workspaces: 2,
      decisions_made: 15,
      knowledge_assets: 45,
      active_users: 8
    };
  },

  // Workspaces
  async getWorkspaces(orgId) {
    const response = await axiosInstance.get(`/organizations/${orgId}/workspaces`);
    return response.data.data.map(w => ({
      ...w,
      decisions_count_30d: 10,
      knowledge_assets_count: 120,
      active_users_count: 5,
      last_activity: '1 day ago'
    }));
  },

  async createWorkspace(name, description, goal, successMetrics, decisionPoints) {
    const response = await axiosInstance.post('/workspaces', { 
      name, 
      description, 
      goal, 
      success_metrics: successMetrics, 
      decision_points: decisionPoints 
    });
    return response.data.data;
  },

  async updateWorkspace(workspaceId, updatedWorkspace) {
    const response = await axiosInstance.patch(`/workspaces/${workspaceId}`, updatedWorkspace);
    return response.data.data;
  },

  async importKnowledgeToWorkspace(workspaceId, assetIds) {
    const response = await axiosInstance.post(`/workspaces/${workspaceId}/knowledge`, { asset_ids: assetIds });
    return response.data.data;
  },

  // Knowledge
  async getKnowledgeAssets(workspaceId = null) {
    const response = await axiosInstance.get('/knowledge/assets');
    return response.data.data;
  },

  async uploadKnowledge(workspaceId, orgId, description, file, chunkingStrategy = null, chunkProfile = null, schemaId = null) {
    const formData = new FormData();
    if (workspaceId) formData.append('workspace_id', workspaceId);
    formData.append('organization_id', orgId);
    formData.append('description', description);
    formData.append('file', file);
    
    if (chunkingStrategy) formData.append('chunking_strategy_override', chunkingStrategy);
    if (chunkProfile) formData.append('chunk_profile_override', chunkProfile);
    if (schemaId) formData.append('schema_id_override', schemaId);
    
    const response = await axiosInstance.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data.data;
  },

  async analyzeKnowledge(workspaceId, orgId, description, file, schemaId = null) {
    const formData = new FormData();
    if (workspaceId) formData.append('workspace_id', workspaceId);
    formData.append('organization_id', orgId);
    formData.append('description', description);
    formData.append('file', file);
    if (schemaId) formData.append('schema_id', schemaId);
    
    const response = await axiosInstance.post('/knowledge/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data.data;
  },

  // Decisions
  async getDecisions(workspaceId) {
    const response = await axiosInstance.get(`/decisions`, { params: { workspace_id: workspaceId } });
    return response.data.data;
  },

  async getDecision(decisionId) {
    const response = await axiosInstance.get(`/decisions/${decisionId}`);
    return response.data.data;
  },

  async executeDecision(workspaceId, userRequest) {
    const response = await axiosInstance.post('/decisions/execute', { workspace_id: workspaceId, user_request: userRequest });
    return response.data.data;
  },

  async resumeDecision(decisionId, approved, feedback) {
    const response = await axiosInstance.post(`/decisions/${decisionId}/resume`, { approved, feedback });
    return response.data.data;
  },

  async recordOutcome(decisionId, humanDecision, feedback, finalOutcome = null) {
    const payload = { decision_id: decisionId, human_decision: humanDecision, feedback };
    if (finalOutcome) payload.final_outcome = finalOutcome;
    const response = await axiosInstance.post('/decisions/outcome', payload);
    return response.data.data;
  },

  // Rules
  async getRules(workspaceId) {
    const response = await axiosInstance.get(`/workspaces/${workspaceId}/rules`);
    return response.data.data;
  },

  async createRule(workspaceId, orgId, rule) {
    const payload = {
      workspace_id: workspaceId,
      name: rule.name,
      description: rule.details,
      rule_type: 'hard_filter', // defaulting to hard_filter for now, but UI doesn't explicitly have it mapped perfectly
      conditions: [{ field_name: "custom_rule", operator: "exists", value: null }], // dummy condition
      priority: rule.priority,
    };
    const response = await axiosInstance.post(`/workspaces/${workspaceId}/rules`, payload);
    return response.data.data;
  },

  async deleteRule(workspaceId, ruleId) {
    const response = await axiosInstance.delete(`/workspaces/${workspaceId}/rules/${ruleId}`);
    return response.data.data;
  }
};
